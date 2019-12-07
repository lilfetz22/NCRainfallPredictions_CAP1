#!/usr/bin/env python
#

from os import path as p
from os import sep as ossep
from os import remove as del_file
from os import listdir as ls
from sys import stderr
from sys import argv as argslist
from sys import maxsize as registersize
from getpass import getuser
from shutil import move as mv
from re import compile as regex
from platform import system as get_os
from time import sleep
import subprocess


def eprint(*args, **kwargs):
    print(*args, file=stderr, flush=True, **kwargs)

def usage(printTo=""):
	this_file = p.basename(p.abspath(__file__))
	printFn = print if printTo == "stdout" else eprint
	printFn("Usage: ./{0} [-h | --help]".format(this_file))
	exit(1)

def help():
    print("")
    print(" Ansible on Cygwin Configuration Script ")
    print("----------------------------------------")
    print("This script simplifies the user burden of manually installing each "+
		  "package into cygwin.  This will execute the commands to set up the "+
		  "package alias and $PATH variable in ~/.bash_profile & ~/.bashrc.  Then "+
		  "it will execute a sequential install of ansible related dependent "+
		  "packages into the Cygwin environment.  Lastly, it will run a pip "+
		  "install of the ansible package."+'\n\n'+
		  "Requirements: \n"+
		  "   1. Run with Administrator privileges.\n"+
		  "   2. Run from Windows OS proper (PowerShell recommended)\n"+
		  "   3. Cygwin installed at {}".format(dir_cygwin)+
		  "   4. Cygwin installer (setup*.exe) stored as {}".format(dir_cygwin, 'cyg-get', 'cyg-pkg-mgnr.exe')+
		  '\n')
    try: 
        usage(printTo="stdout")
    except SystemExit:
        print("")
    print("Available Options: ")
    print("  -h | --help     Help")
    print("")
    exit(0)

# Process line arguments
def process_args( args ):

	# Argument Handlers
	def request_help(i):
		help()
	def end_args(i):
		return("end_args")
	def unknown(i):
		usage()

	switcher = {
		'-h' :        request_help,
		'--help' :    request_help,
		'/h' :		  request_help,
		'--' : 		  end_args
	}

	for i in range(1,len(args)):
		try:
			func = switcher[args[i]]
			retVal = func(i)
			if retVal == "end_args":
				break
		except KeyError:
			unknown(i)
		except SystemExit as exitrequest:
			raise(exitrequest)
		
	## // If-statements to check if interdependent options are satisfied // ##
	
	## // IF-statements to fill all vars with defaults if not already filled // ##


def check_prereqs():
	print("Checking script environment...")
	compatible_os = regex(r'Windows')
	if not compatible_os.match(get_os()):
		eprint("FAILED: This script only works on Windows with cygwin installed.")
		exit(-1)
	else:
		try:
			# Check cygwin's bash.exe exist
			subprocess.check_call([ 
				'powershell.exe',
				'try {{ if (-not ([System.IO.File]::Exists("{cygwin_path}"))) {{ throw "Error" }} }} catch {{ }};'.format(
					cygwin_path=p.join(dir_cygwin,'bin',"bash.exe")
				)], 
				shell=False
			)
			# Check running as administrator (only Administrator rights can see the temp dir)
			ls(p.join(ossep, 'Windows', 'temp'))

		except subprocess.CalledProcessError:
			eprint("MISSING PREREQ: cygwin not found @ {}/".format(dir_cygwin))
			exit(-2)
		except PermissionError:
			eprint('\n'+"FAILED: Script needs to be run with administrator privileges.")
			eprint("PowerShell w/ Admin Privalages command: \n\t Start-Process powershell -Verb RunAs")
			exit(-3)
		
		# Check cygwin's package manager exists
		pkgmgnr = p.join(dir_cygwin,'cyg-get',"cyg-pkg-mgnr.exe")
		if not p.isfile(pkgmgnr):
			eprint("MISSING PREREQ: cyg-pkg-mgnr.exe not found @ {}/".format(p.join(dir_cygwin, 'cyg-get')))
			if p.isfile(p.join(p.dirname(pkgmgnr), 'setup-x86{}.exe'.format("_64" if is_64bit else ""))):
				# HELPING: original download file found, not renamed.
				eprint("  Please rename setup-x86{}.exe to cyg-pkg-mgnr.exe and try again.\n".format("_64" if is_64bit else ""))
			exit(-4)

	# VALID Environment
	print("PASS")


## ACTION FUNCTION
## Configure aliases in ~/.bashrc
##   - package manager alias
def add_alias():
	print("Adding aliases...")
	profile_filename = p.join(dir_cygwin,'home',getuser(),'.bashrc')
	tmp_filename = p.join(dir_cygwin,'home',getuser(),'.~$.bashrc')

	pkgmgnr_alias = 'alias cyg-get="/cyg-get/cyg-pkg-mgnr.exe -q -P"'
	lines2write = [
		"# Set alias for cygwin's package manager",
		pkgmgnr_alias,
		''
	]

	line2match = regex(r'^# Some example alias instructions')
	prev_complete_match = regex(r'^'+lines2write[0]) 

	def insertAliasConfig(line, newfile, logdata):
		if 'found' not in logdata:
			logdata['found'] = False
			 
		if not logdata['found'] and line2match.search(line):
			for textentry in lines2write:
				newfile.write(textentry+'\n')
			newfile.write(line)
			logdata['found'] = True
		elif len(line) == 0 and not logdata['found']:
			raise( Exception('ERROR: EOF before match was found in file.') )
		elif prev_complete_match.search(line):
			raise( StopIteration() )
		else:
			newfile.write(line)

	print("Adding pkg manager alias: \n`{0}`".format(pkgmgnr_alias))
	try:
		__modifyfile(profile_filename, tmp_filename, insertAliasConfig)
	except Exception as err:
		eprint("Failed to add alias while modifying {}".format(profile_filename))
		raise(err)


## ACTION FUNCTION
## Configure $PATH variable
def configure_path():
	print("Configuring cygwin $PATH variable...")
	unix_precedence = [ 
		'/usr/local/bin',
		'/usr/bin',
		'/bin',
		'/usr/sbin',
		'/sbin'
	]

	path_assignment = 'PATH="'+':'.join(unix_precedence)+':${PATH}"'
	lines2write = [
		'# Set default path variable',
		path_assignment,
		''
	]

	line2match = regex(r'^# Set PATH so it includes user\'s private bin')
	prev_complete_match = regex(r'^'+lines2write[0]) 

	bashprofilefile = p.join(dir_cygwin,'home',getuser(),'.bash_profile')
	tmpfile = p.join(dir_cygwin,'home',getuser(),'.~$.bash_profile')

	def insertPathConfig(line, newfile, logdata):
		if 'found' not in logdata:
			logdata['found'] = False
			 
		if not logdata['found'] and line2match.search(line):
			for textentry in lines2write:
				newfile.write(textentry+'\n')
			newfile.write(line)
			logdata['found'] = True
		elif len(line) == 0 and not logdata['found']:
			raise( Exception('ERROR: EOF before match was found in file.') )
		elif prev_complete_match.search(line):
			raise( StopIteration() )
		else:
			newfile.write(line)

	try:
		__modifyfile(bashprofilefile, tmpfile, insertPathConfig)
	except Exception as err:
		eprint("Failed to modify {}".format(bashprofilefile))
		raise(err)

## HELPER FUNCTION
## Generically opens a file, copies to a temporary file line by line, 
##   allows external function insertion before replacing original file
def __modifyfile(filename, tmpfilename, processline_Fn):
	try:
		origf = open(filename, "r")
		newf = open(tmpfilename, "w+")
		
		persistentdata = {}
		while True:
			line = origf.readline()
			if len(line) == 0:	# EOF
				processline_Fn(line, newf, persistentdata)
				break
			else:
				processline_Fn(line, newf, persistentdata)

	except StopIteration:
		print("Verified File: {}".format(filename))
		newf.close()
		newf = None
		del_file(tmpfilename)
		return()
	except Exception as err:
		eprint(err)
		newf.close()
		newf = None
		del_file(tmpfilename)		# delete tmp file
	finally:
		origf.close()
		if newf is not None:
			newf.close()

	pathsplitter = regex(r'\\')
	pathmapper = regex(r'^C:/(.*)$')
	cygwin_filename = pathmapper.sub(	# swap filename to path from inside cygwin
		'/cygdrive/c/\\1', 
		'/'.join(
			pathsplitter.split(tmpfilename)
		)
	)
	try:
		# convert file type with dos2unix
		exitcode = __runcygcmd("/usr/bin/dos2unix.exe {file}".format(file=cygwin_filename))
		if exitcode != 0:
			raise( Exception("Failed to convert file to unix file.") )
		
		# replace original file
		mv( tmpfilename, filename )

	except Exception as err:
		eprint(err)
		raise(err)
	else:
		print("Modified: {}".format(filename))

## HELPER FUNCTION
## Spawn a subprocess that will execute in cygwin's bash.exe
def __runcygcmd(cygcmd=""):
	cygwin_bash = p.join(dir_cygwin,'bin',"bash.exe")
	if cygcmd == "":
		raise(Exception("__runcygcmd(): no command provided."))

	print("[bash.exe] $> "+cygcmd)
	try:
		pbash = subprocess.Popen(
			[cygwin_bash, '-c', "source $HOME/.bash_profile && {cmd}".format(cmd=cygcmd)], 
			shell=False,
		)
		maximum_runtime = 60*25  # 25 min
		proceedregex = regex(r'^(y|yes|Y|YES)$')
		while True:
			try:
				pbash.wait(timeout=maximum_runtime)
			except subprocess.TimeoutExpired as err:
				answer = input('\n'+"Max runtime (25m) exceeded, do you want to kill the process (Y/n)?"+' ')
				if proceedregex.match(answer) and pbash.poll() is None:
					pbash.kill()
					raise(err)
				else:
					print("Ok! Waiting...")
			else:
				return(pbash.returncode)

	except KeyboardInterrupt as usr_canx:
		raise(usr_canx)
	except Exception as err:
		raise(err)
	else:
		pass

## HELPER FUNCTION
## Spawn a subprocess that will run a check for an installed package
def __is_pkg_installed(pkgname=""):
	cygwin_bash = p.join(dir_cygwin,'bin',"bash.exe")
	if pkgname == "":
		raise(Exception("__is_pkg_installed(): no command provided."))

	pkgcheckcmd = "/usr/bin/cygcheck --check-setup {pkg} ".format(pkg=pkgname) \
			     +"| /usr/bin/awk -F \"[ ][ ]+\" 'NR>=3 {print $3}'"
	try:
		print("[bash.exe] $> "+pkgcheckcmd)
		pbash_stdout = subprocess.check_output(
			[cygwin_bash, '-c', "source $HOME/.bash_profile && {cmd}".format(cmd=pkgcheckcmd)],
			shell=False,
			universal_newlines=True,	# forces stdout to be a string
			timeout=15
		)
		return( True if pbash_stdout.strip() == "OK" else False )

	except KeyboardInterrupt as usr_canx:
		raise(usr_canx)
	except Exception as err:
		raise(err)
	else:
		pass


## ACTION FUNCTION
## Install dos2unix.exe package for file conversions
def install_utilities():
	print("Installing Utilities...")
	utilities = [
		{ 'pkg':'dos2unix', 'prompt':True,'prompt_text':"Has the installation completed yet (Y/n)?" }
	]

	is_first_loop = True
	for utility in utilities:
		while True:
			try:
				if __is_pkg_installed(utility['pkg']):  # if needed, step 2
					print("VERIFIED: {pkg} {adj} installed.".format(pkg=utility['pkg'], adj=('already' if is_first_loop else '')))
					break

				elif not is_first_loop:  # on 1 & 2 failure, step 3
					raise( StopIteration('FAILURE: utility {} could not be installed.'.format(utility['pkg'])) )

				else:  # likely step 1
					print("Installing {}...".format(utility['pkg']))
					exitcode = __runcygcmd("/cyg-get/cyg-pkg-mgnr.exe -q -P {}".format(utility['pkg']))
					if exitcode != 0:
						raise( subprocess.SubprocessError("Utility '{}' returned a failed exit status ({})".format(utility['pkg'], exitcode)) )
					else:
						break		# installation went fine
				
			except subprocess.SubprocessError as err:
				eprint(err)
				if is_first_loop:
					is_first_loop = False
					continue		# try again to verify installation
				else:
					raise(err)		# likely completely other error
			except StopIteration as err:
				e = Exception(str(err))   # re-wrap error
				raise(e)
	
	print("INSTALLED: Utilities in cygwin")
	# END of install_utilities


## HELPER FUNCTION
## Install ansible dependencies
## requires cyg-get alias to exist
def __install_ansible_dep():
	print('Installing ansible package dependencies...')
	dependencies = [ 
		'cygwin32-gcc-g++',  
        'gcc-core',
        'gcc-g++',
        'git',
        'libffi-devel',
        'nano',
		'openssl',
        'python3',
        'python3-devel',
        'python36-crypto',
        'python36-openssl',
        'python36-pip',
        'python36-setuptools',
        'tree'
	]
	pipfinder = regex(r'-pip$')

	for d in range(len(dependencies)):
		dep = dependencies[d]
		print("Dependency {i} of {total} ({pkg})".format(i=d+1,total=len(dependencies),pkg=dep))
		is_first_loop = True
		
		while True:
			try:
				if __is_pkg_installed(dep):  # if needed, step 2
					print("VERIFIED: {dependency} {adj} installed.".format(dependency=dep, adj=('already' if is_first_loop else '')))
					break
				
				elif not is_first_loop:  # on 1 & 2 failure, step 3
					raise( StopIteration('FAILURE: dependency {} could not be installed.'.format(dep)) )
				
				else:  # likely step 1
					print("Installing {}...".format(dep))
					exitcode = __runcygcmd("/cyg-get/cyg-pkg-mgnr.exe -q -P {}".format(dep))
					if exitcode != 0:
						raise( subprocess.SubprocessError("Dependency '{}' returned a failed exit status ({})".format(dep, exitcode)) )
					else:
						break		# installation went fine
				
			except subprocess.SubprocessError as err:
				eprint(err)
				if is_first_loop:
					is_first_loop = False
					continue		# try again to verify installation
				else:
					raise(err)		# likely completely other error
			except StopIteration as err:
				e = Exception(str(err))   # re-wrap error
				raise(e)

		if pipfinder.search(dep):
			# add pip pointer
			if __runcygcmd("ln -s /usr/bin/pip3 /usr/local/bin/pip") != 0:
				raise( Exception("Failed to add pip symbolic link") )
			else:
				print("Created symlink to pip3 as at /usr/local/bin/pip")
	
	print("INSTALLED: Ansible dependencies in cygwin")
	# END of __install_ansible_dep


## ACTION FUNCTION
## Install ansible
def install_ansible():
	print("Installing Ansible...")
	config_actions = [ 
		{ 'fn'  : __install_ansible_dep, 'onerror':"FAILED: Dependency package installations into cygwin" },
		# required python library for the gce ansible module's communication
		{  
			'cmd' : "pip install requests",
			'onerror': "FAILED: pip installation of requests library into cygwin"
		},
		{
			'cmd' : "pip install google-auth",
			'onerror': "FAILED: pip installation of google-auth library into cygwin"
		},
		{
			'cmd' : "pip install ansible",
			'onerror':"FAILED: pip installation of Ansible into cygwin" 
		}
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
			eprint( action['onerror'] )
			raise(err)

	# End ansible install
	print("SUCCESS: Ansible installed")


def cygwin_configure():
	config_actions = [ 
		{ 'fn':install_utilities, 'onerror':"FAILED: installation of utilities in cygwin" },
		{ 'fn':configure_path, 'onerror':"FAILED: configuration of $PATH variable in cygwin" },
		{ 'fn':add_alias, 'onerror':"FAILED: configuration of bash aliases in cygwin" },
		{ 'fn':install_ansible, 'onerror':"FAILED: Ansible installation into cygwin" }
	]

	for action in config_actions:
		try:
			action['fn']()
		except KeyboardInterrupt:
			eprint('\n'+"User interrupted configuration process.  Exiting...")
			exit(1)
		except:
			eprint( action['onerror'] )
			exit(1)

	# Validation
	try:
		if __runcygcmd('command -v ansible') != 0:
			raise(Exception("TEST (ansible verification):\t FAILED"))
		else:
			print("TEST (ansible verification):\t SUCCESS")
			
	except Exception as err:
		eprint(err)
		eprint('\n'+"Check installation steps & reinstall, "+
			  "if still is an issue, "+
			  "please submit a issue to github.com/codejedi365/CapstoneProject1.", file=stderr, flush=True)
		exit(2)


## AS MAIN SCRIPT
if __name__ == "__main__":
	is_64bit = True if registersize > 2**32 else False
	dir_cygwin = p.join(p.abspath(ossep), 'cygwin' + ('64' if is_64bit else '32'))

	try:
		process_args(argslist)

		check_prereqs()

		cygwin_configure()

	except KeyboardInterrupt:
		eprint('\n'+"User interrupted configuration process.  Exiting...")
		exit(1)

