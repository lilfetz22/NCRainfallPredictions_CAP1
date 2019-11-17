#!/usr/bin/env python
#

from os import path as p
from os import sep as ossep
from sys import stderr
from shutil import move as mv
from re import compile as regex
from platform import system as get_os
import subprocess


## ACTION FUNCTION
## Configure aliases in ~/.bashrc
##   - package manager alias
def add_alias():
	profile_filename = p.expanduser('~/.bashrc')
	tmp_filename = p.expanduser('~/.~$.bashrc')
	pkgmgnr_alias = 'alias cyg-get="/cyg-get/setup-x86_64.exe -P"'
	line2match = regex(r'^# Some example alias instructions')

	found = False
	def insertAliasConfig(line, newfile):
		if not found and line2match.search(line):
			newfile.write("# Set alias for cygwin's package manager")
			newfile.write(pkgmgnr_alias)
			newfile.write('\n\n')
			newfile.write(line)
			found = True
		else:
			newfile.write(line)

	try:
		__modifyfile(profile_filename, tmp_filename, insertAliasConfig)
	except Exception as err:
		print("Failed to add alias while modifying {}".format(profile_filename))
		raise(err)


## ACTION FUNCTION
## Configure $PATH variable
def configure_path():
	unix_precedence = [ 
		'/usr/local/bin',
		'/usr/bin',
		'/bin',
		'/usr/sbin',
		'/sbin'
	]

	path_assignment = 'PATH="'+':'.join(unix_precedence)+'$\{PATH\}"'
	line2match = regex(r'^# Set PATH so it includes users\'s private bin')

	bashprofilefile = p.expanduser('~/.bash_profile')
	tmpfile = p.expanduser('~/.~$.bash_profile')

	found = False
	def insertPathConfig(line, newfile):
		if not found and line2match.search(line):
			newfile.write("# Set default path variable")
			newfile.write(path_assignment)
			newfile.write('\n\n')
			newfile.write(line)
			found = True
		else:
			newfile.write(line)

	try:
		__modifyfile(bashprofilefile, tmpfile, insertPathConfig)
	except Exception as err:
		print("Failed to modify {}".format(bashprofilefile))
		raise(err)

## HELPER FUNCTION
## Generically opens a file, copies to a temporary file line by line, 
##   allows external function insertion before replacing original file
def __modifyfile(filename, tmpfilename, processline_Fn):
	try:
		origf = open(filename, "r")
		newf = open(tmpfilename, "w") 

		while True:
			line = f.readline()
			if line == '':	# EOF
				break
			else:
				processline_Fn(line, newf)

	except:
		newf.close()
		# delete tmp file
	finally:
		origf.close()
		if newf is not None:
			newf.close()

	try:
		mv( tmpfilename, filename )
	except Exception as err:
		print(err)
		raise(err)
	else:
		print("Modified: {}".format(filename))

## HELPER FUNCTION
## Spawn a subprocess that will execute in cygwin's bash.exe
def __runcygcmd(cygcmd=""):
	cygwin_bash = p.join(p.abspath(ossep),'cygwin64','bin',"bash.exe")
	if cygcmd == "":
		raise(Exception("__runcygcmd(): no command provided."))

	print("[bash.exe] $> "+cygcmd)
	try:
		pbash = subprocess.Popen(
			[cygwin_bash, '-c', "source $HOME/.bash_profile && {cmd}".format(cmd=cygcmd)], 
			shell=False,
		)
		maximum_runtime = 60*8  # 8 min
		try:
			pbash.wait(timeout=maximum_runtime)
		except subprocess.TimeoutExpired as err:
			pbash.kill()
			raise(err)
		else:
			return(pbash.returncode)

	except KeyboardInterrupt as usr_canx:
		raise(usr_canx)
	except Exception as err:
		raise(err)
	else:
		pass

## HELPER FUNCTION
## Install ansible dependencies
## requires cyg-get alias to exist
def __install_ansible_dep():
	dependencies = [ 
		'cygwin32-gcc-g++',  
        'gcc-core',
        'gcc-g++',
        'git',
        'libffi-devel',
        'nano',
        'python3',
        'python3-devel',
        'python36-crypto',
        'python36-openssl',
        'python36-pip',
        'python36-setuptools',
        'tree'
	]
	pipfinder = regex(r'-pip$')

	for dep in dependencies:
		try:
			exitcode = __runcygcmd("cyg-get {}".format(dep))
			if exitcode != 0:
				raise( Exception("Dependency '{}' returned a failed exit status".format(dep)) )
			elif pipfinder.match(dep):
				# add pip pointer
				if __runcygcmd("ln -s /usr/bin/pip3 /usr/bin/pip") != 0:
					raise( Exception("Failed to add pip symbolic link") )
			else:
				continue
		except Exception as err:
			print( err, file=stderr, flush=True )
			raise(err)
	
	print("INSTALLED: Ansible dependencies in cygwin")
	# END of __install_ansible_dep


## ACTION FUNCTION
## Install ansible
def install_ansible():
	config_actions = [ 
		{ 'fn'  : __install_ansible_dep, 'onerror':"FAILED: Dependency package installations into cygwin" },
		{ 'cmd' : "pip install ansible", 'onerror':"FAILED: pip installation of Ansible into cygwin" }
	]

	for action in config_actions:
		try:
			if 'fn' in action:
				action['fn']()
			elif 'cmd' in action:
				if __runcygcmd(action['cmd']) != 0:
					raise(Exception("cygcmd ({}) returned a failed exitcode.".format(action['cmd'])))
			else:
				continue
		except Exception as err:
			print( action['onerror'], file=stderr, flush=True )
			raise(err)

	# End ansible install
	print("SUCCESS: Ansible installed")


## AS MAIN SCRIPT
if __name__ == "__main__":
	compatible_os = regex(r'Windows')
	if not compatible_os.match(get_os()):
		print("FAILED: This script only works on Windows with cygwin installed.", file=stderr, flush=True)
		exit(-1)
	else:
		try:
			subprocess.check_call([ 
				'powershell.exe',
				'if (-not ([System.IO.File]::Exists("{cygwin_path}"))) { throw "Error" }'.format(
					cygwin_path=p.join(p.abspath(ossep),'cygwin64','bin',"bash.exe")
				)], 
				shell=False
			)
		except subprocess.CalledProcessError:
			print("MISSING PREREQ: cygwin not found @ {}/".format(p.join(p.abspath(ossep),'cygwin64')), file=stderr, flush=True)
			exit(-2)

	# VALID Environment
	config_actions = [ 
		{ 'fn':configure_path, 'onerror':"FAILED: configuration of $PATH variable in cygwin" },
		{ 'fn':add_alias, 'onerror':"FAILED: configuration of bash aliases in cygwin" },
		{ 'fn':install_ansible, 'onerror':"FAILED: Ansible installation into cygwin" }
	]

	for action in config_actions:
		try:
			action['fn']()
		except:
			print( action['onerror'], file=stderr, flush=True )
			exit(1)

	# Validation
	try:
		if __runcygcmd('command -v ansible') != 0:
			raise(Exception("TEST (ansible verification):\t FAILED"))
		else:
			print("TEST (ansible verification):\t SUCCESS")
			
	except Exception as err:
		print(err, file=stderr, flush=True)
		print("Check installation steps & reinstall, "+
			  "if still is an issue, "+
			  "please submit a issue to github.com/codejedi365/CapstoneProject1.", file=stderr, flush=True)
		exit(2)
