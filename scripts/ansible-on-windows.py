#!/usr/bin/env python3

#
#
# make sure /etc/skel files are transferred over and setup
# complete rest of ansible install

# On failure, blow away directory
# blow away file on invalid verification or user cancelation


from os import path as p
from os import sep as ossep
from os import chdir as cd
from os import remove as rm
from os import listdir as ls
from os import makedirs as mkdirs
from sys import stderr
from sys import argv as argslist
from sys import maxsize as registersize
from re import compile as regex
from platform import system as get_os
from shutil import rmtree as shutil_rmtree
from urllib.parse import urljoin
import urllib.request
import subprocess
import base64
import cygwin_configure


public_key_file = p.join(p.dirname(p.realpath(__file__)), 'cygwin_pubring.asc')


def eprint(*args, **kwargs):
	''' 
	Prints messages to stderr
	'''
	print(*args, file=stderr, flush=True, **kwargs)

def vprint(*args, **kwargs):
	''' 
	Prints messages of verbosity level 1
	'''
	_vprint(1, *args, **kwargs)
	
def vvprint(*args, **kwargs):
	''' 
	Prints messages of verbosity level 2
	'''
	_vprint(2, *args, **kwargs)

def vvvprint(*args, **kwargs):
	''' 
	Prints messages of verbosity level 3
	'''
	_vprint(3, *args, **kwargs)

def _vprint(msglvl, *args, **kwargs):
	'''
	Prints messages according to global verbosity level and level of message.
	VERBOSE Cases:
		1. When global verbosity is set to a value, then only messages that are less than or equal to the verbosity level are printed.
		2. When global verbosity is set to True, then all messages are printed
		3. When global verbosity is set to False, no messages are printed
	param: msglvl, Integer
	param: *args, Pass-through print() args
	param: **kwargs, Pass-through print() keyword args
	'''
	vlevel = VERBOSE if not isinstance(VERBOSE, bool) else (msglvl if VERBOSE else 0)
	if (vlevel - msglvl) >= 0:
		print(*args, **kwargs)


def usage(printTo=""):
	this_file = p.basename(p.abspath(__file__))
	printFn = print if printTo == "stdout" else eprint
	printFn("Usage: ./{0} [-h | --help]".format(this_file))
	exit(1)


def help():
    print("")
    # print(" Ansible on Cygwin64 Configuration Script ")
    # print("------------------------------------------")
    # print("This script simplifies the user burden of manually installing each "+
	# 	  "package into cygwin.  This will execute the commands to set up the "+
	# 	  "package alias and $PATH variable in ~/.bash_profile & ~/.bashrc.  Then "+
	# 	  "it will execute a sequential install of ansible related dependent "+
	# 	  "packages into the Cygwin environment.  Lastly, it will run a pip "+
	# 	  "install of the ansible package."+'\n\n'+
	# 	  "Requirements: \n"+
	# 	  "   1. Run with Administrator privileges.\n"+
	# 	  "   2. Run from Windows OS proper (PowerShell recommended)\n"+
	# 	  "   3. Cygwin installed at C:\\cygwin64\\ "+
	# 	  '\n')
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
	error_count = 0	
	print("Checking script environment...")
	compatible_os = regex(r'Windows')
	if not compatible_os.match(get_os()):
		eprint("FAILED: This script only works on Windows with administrator privileges.")
		error_count -= 1
	else:
		try:
			# Check running as administrator (only Administrator rights can see the temp dir)
			ls(p.join(ossep, 'Windows', 'temp'))

		except PermissionError:
			eprint('\n'+"FAILED: Script needs to be run with administrator privileges.")
			eprint("PowerShell w/ Admin Privalages command: \n\t Start-Process powershell -Verb RunAs")
			error_count -= 1

	# VALID Environment
	if error_count != 0:
		return(error_count)
	else:
		print("PASS")
		return(0)


def setup_user():
	cygwin_bash = p.join(dir_cygwin,'bin',"bash.exe")
	cmds = [
		' '.join(['/bin/cp', '-r', '/etc/skel/*', '$HOME/'])
	]

	vprint("Setting up user profile in cygwin...")
	for cygcmd in cmds:
		vvprint("[bash.exe] $> "+cygcmd)
		try:
			pbash = subprocess.check_call(
				[cygwin_bash, '-c', cygcmd],
				shell=False,
			)
		except Exception as err:
			raise(err)
		else:
			pass
	vprint("Cygwin user profile setup completed.")


def verify_installation():
	try:
		# Check cygwin64's bash.exe exist
		subprocess.check_call([ 
			'powershell.exe',
			'if (-not ([System.IO.File]::Exists("{cygwin_path}"))) {{ throw "Error" }}'.format(
				cygwin_path=p.join(dir_cygwin,'bin',"bash.exe")
			)], 
			shell=False
		)

	except subprocess.CalledProcessError:
		eprint("INSTALLATION FAILED: cygwin's bash.exe not found @ {}/".format(p.join(p.abspath(ossep),'cygwin64')))
		exit(-2)


def verify_sign(public_key_loc, signature, data):
    '''
    Verifies with a public key from whom the data came that it was indeed 
    signed by their private key
    param: public_key_loc Path to public key
    param: signature String signature to be verified
    return: Boolean. True if the signature is valid; False otherwise. 
    '''
    from Crypto.PublicKey import RSA 
    from Crypto.Signature import PKCS1_v1_5 
    from Crypto.Hash import SHA256
    pub_key = open(public_key_loc, "r").read() 
    rsakey = RSA.importKey(pub_key) 
    signer = PKCS1_v1_5.new(rsakey) 
    digest = SHA256.new() 
    # Assumes the data is base64 encoded to begin with
    digest.update(base64.b64decode(data)) 
    if signer.verify(digest, base64.b64decode(signature)):
        return True
    return False


def install_cygwin():

	try:
		# Check cygwin64's bash.exe already exists
		subprocess.check_call([ 
			'powershell.exe',
			'if (-not ([System.IO.File]::Exists("{cygwin_path}"))) {{ throw "Error" }}'.format(
				cygwin_path=p.join(dir_cygwin,'bin',"bash.exe")
			)], 
			shell=False
		)
		if FORCE:
			shutil_rmtree(dir_cygwin, ignore_errors=True)
			raise(subprocess.CalledProcessError(-1,None))
	except subprocess.CalledProcessError:
		pass
	else:
		print("FOUND: Cygwin is already installed.")
		return(0)
	
	# Download Cygwin package when not found
	# Based on 32 bit or 64 bit windows
	# make directory path C:\cygwin64\cyg-get\
	# change working directory 
	# download the correct exe and signature file
	# verify downloaded file with public key

	# spawn setup file for user
	# wait until user says it is done to run the configuration
	#  --- make sure to run checks from configuration first

	dir_installer = p.join(dir_cygwin,'cyg-get')
	if not p.isdir(dir_installer):
		vprint("Creating Directories: ")
		vprint("  "+dir_cygwin)
		vprint("  "+dir_installer+ossep)
		
		mkdirs(dir_installer)
	# End IF

	# Change current working directory
	vprint("Changing working directory")
	vvprint("$PWD = {}".format(dir_installer))
	cd(dir_installer)

	# Default Download handler
	def write2file(download,spec):
		with open(spec['output'], 'w+') as o:
			while True:
				bytes = download.read(256)
				if bytes is None:
					break
				o.write(bytes)
	# 
	def exe_download_handler(download,spec):
		write2file(download, spec)
		f = open(spec['output'],'r').read()
		if not verify_sign(public_key_file, vars['exe.sig'], f):
			raise( Exception("") )

	# Download the correct exe and signature file
	base_url = 'https://www.cygwin.com'
	exefile_uri = 'setup-x86{}.exe'.format(("" if not is_64bit else "_64"))

	vars = {}
	dwnloads = [
		{	# signature file
			'uri': '{}.sig'.format(exefile_uri),
			'name': 'exe.sig',
			'content-type': 'application/pgp-signature',
			'output': lambda dwnload: base64.b64encode(dwnload.read()),
			'handler': lambda dwnload, spec: spec['output'](dwnload)
		},
		{	# exefile
			'uri': exefile_uri,
			'name': 'exefile',
			'content-type': 'application/octet-stream',
			'output': 'cyg-pkg-mgnr.exe',
			'handler': exe_download_handler
		}
	]
	status_translations = {
		'200': "OK",
		'301': "Moved Permanently",
		'400': "Bad Request",
		'401': "Not Authorized",
		'403': "Forbidden",
		'404': "Not Found",
		'500': "Internal Server Error"
	}

	vprint("Downloading files...")
	for dwnloadspec in dwnloads:
		vvprint("\t Downloading {}".format(urljoin(base_url,dwnloadspec['uri'])))
		try:
			dwnload = urllib.request.urlopen(
				urljoin(base_url, dwnloadspec['uri'])
			)
			vvprint("HTTP {code} {eng}".format(
				code=dwnload.getcode(),
				eng=status_translations[str(dwnload.getcode())] 
			))
			if dwnload.getcode() != 200:		# Check HTTP Status Code
				raise(Exception("HTTP Response error ({})".format(
					' '.join([str(dwnload.getcode()), status_translations[str(dwnload.getcode())]])
				)))
			elif dwnload.getheader('Content-Type') != dwnloadspec['content-type']:
				raise(Exception("HTTP Content-Type: {0} != {1} (expected)".format(
					dwnload.getheader('Content-Type'),
					dwnloadspec['content-type']
				)))
			else:
				if dwnloadspec['handler'] is None:  # Default - push to file
					vvvprint("Default response handler: write2file()")
					write2file(dwnload, dwnloadspec)
				else:
					vvvprint("Response handler: custom")
					dwnloadspec['handler'](dwnload, dwnloadspec)

				# Set variable as found output
				vars[dwnloadspec['name']] = dwnloadspec['output']
				vvvprint("SET vars['{}']".format(dwnloadspec['name']))

		except KeyboardInterrupt as usr_canx:
			eprint("Reverting...")
			shutil_rmtree(dir_cygwin)
			raise(usr_canx)
		except Exception as err:
			eprint(err)
			### TODO
			# Handle HTTP exceptions
			# Handle invalid content-type
			
			# Handle invalid signature
			if 'exefile' in vars or dwnloadspec['name'] == 'exefile':
				# Delete downloaded file
				rm(p.join(dir_installer, dwnloadspec['output']))

			raise(err)


	# spawn validated installer program for user

	print("Opening Cygwin Installer...")
	try:
		vprint("Spawning {}".format(vars['exefile']))
		vvvprint("Opened user dialog, program stdout/stderr: ")
		pinstaller = subprocess.Popen(
			vars['exefile'], 
			shell=False
		)
		proceedregex = regex(r'^(y|yes|Y|YES)$')
		while True:
			try:
				pinstaller.wait(60)
			except subprocess.TimeoutExpired as err:
				if pinstaller.poll() is not None:
					answer = input('\n'+"Has the installer dialog completed installation (Y/n)?"+' ')
					if proceedregex.match(answer):
						break
					else:
						print("Ok! Waiting...")
			else:
				vprint("Cygwin installer process complete.")
				break

	except KeyboardInterrupt as usr_canx:
		pinstaller.kill()
		raise(usr_canx)
	except Exception as err:
		raise(err)
	else:
		pass



## AS MAIN SCRIPT
if __name__ == "__main__":
	MODE_QUIET = False
	VERBOSE = True
	FORCE = False
	is_64bit = True if registersize > 2**32 else False
	dir_cygwin = p.join(p.abspath(ossep), 'cygwin' + ('64' if is_64bit else '32'))
	vvvprint("{}-bit detected.".format('64' if is_64bit else '32'))
	vvvprint("Target Cygwin installation directory: \n\t {}".format(dir_cygwin))

	config_actions = [ 
		{ 'fn':install_cygwin, 'onerror':"FAILED: download & installation of cygwin." },
		{ 'fn':verify_installation, 'onerror':"FAILED: verification of cygwin installation." },
		{ 'fn':setup_user, 'onerror':"FAILED: cygwin user profile setup." },
		# { 'fn':cygwin_configure.MAIN, 'onerror':"FAILED: ansible configuration of cygwin." }
	]


	try:
		process_args(argslist)

		if check_prereqs() != 0: 
			exit(1)

		if not MODE_QUIET:
			pass	# print_banner()

		for action in config_actions:
			try:
				action['fn']()
			except KeyboardInterrupt as usr_canx:
				raise(usr_canx)
			except:
				eprint( action['onerror'] )
				exit(1)

	except KeyboardInterrupt as usr_canx:
		eprint('\n'+"User interrupted build process.  Exiting...")
		exit(1)	
	else:
		exit(0)

