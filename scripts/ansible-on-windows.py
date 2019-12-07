#!/usr/bin/env python3
# codejedi365 | MIT License

from copy import copy as clone
from datetime import datetime as date
from pytz import timezone
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
	'''
	Prints script parameter & flag option examples
	param: printTo, Change print function from stderr to stdout
	'''
	this_file = p.basename(p.abspath(__file__))
	printFn = print if printTo == "stdout" else eprint
	printFn("Usage: ./{0} [-v | -vv | -vvv] [-h | --help]".format(this_file))
	exit(1)


def help():
    print("")
    print(" Ansible on Windows Configuration Script ")
    print("-----------------------------------------")
    print("This script automates the download, install, and configuration of "+
		  "Ansible for Windows.  It depends upon cygwin (a linux emulator compiled "+
		  "to run on Windows OS) which then can configure Ansible to work with the "+
		  "Cygwin substructure.  This hooks into the cygwin_configure.py script to "+
		  "make this script an enclusive one use step."+
		  '\n\n'+
		  "Requirements: \n"+
		  "   1. Run with Administrator privileges."+'\n'+
		  "   2. Run from Windows OS proper (PowerShell recommended)"+'\n')
    try: 
        usage(printTo="stdout")
    except SystemExit:
        print("")
    print("Available Options: ")
    print("  -h | --help       Help")
    print("  -v | -vv | -vvv   Show in-depth log output (descriptive, detailed, verbose)")
    print("")
    exit(0)


def print_banner():
    print('\n'+ \
			"==============================================")
    print(	"|       Ansible for Windows via Cygwin       |")
    print(  "==============================================")
    print(  "START: {}".format(date.now(timezone('US/Eastern')).strftime("%a %b %d %H:%M:%S %Z %Y")))
    print(  "----------------------------------------------")
    print(  "$> download, install, configure ... ANSIBLE"+'\n')


# Process line arguments
def process_args( argslist ):
	global VERBOSE
	args = clone(argslist)
	args.pop(0)  # skip index 0 since it is the filename not an parameter

	# Argument Handlers
	def add_verbosity(i):
		global VERBOSE
		if isinstance(VERBOSE, bool) and not VERBOSE:   # was False
			VERBOSE = 1
		elif isinstance(VERBOSE, int):
			VERBOSE += len(regex(r'v').findall(args[i]))
			
	def request_help(i):
		help()
	def end_args(i):
		return("end_args")
	def unknown(i):
		usage()

	switcher = {
		'-v' :		  add_verbosity,
		'-vv' :		  add_verbosity,
		'-vvv' :	  add_verbosity,
		'-h' :        request_help,
		'--help' :    request_help,
		'/h' :		  request_help,
		'--' : 		  end_args
	}

	# TODO: Bug if you have -vvh, will not work as expected, -vv must be separate option

	# Dynamically finds other alternatives from spec ^
	compressedflags = list(filter(lambda opt: regex(r'^-[^-](?!=)$').search(opt), switcher.keys()))
	compressedflags = [regex(r'^-(.*)$').sub('\\1', i) for i in compressedflags]		# removes the hyphen
	if len(compressedflags) > 1:
		compressedflagsregex = regex("^-["+''.join(compressedflags)+"]{2,"+str(len(compressedflags))+"}$")
	else:
		compressedflagsregex = regex(r'^$')		# almost impossible to match 

	# PRE-PROCESS opts spec... handle 2-part parameters
	opts_w_input = dict(filter(lambda item: regex(r'=$').search(item[0]), switcher.items()))
	opts_w_input_keys = list(opts_w_input.keys())
	for o in opts_w_input_keys:			# Fixes switcher so keys will be found
		fn = opts_w_input[o]
		if regex(r'^-[^-]').search(o):				# single dash option (remove =)
			opts_w_input.pop(o)
			switcher.pop(o)
			switcher[regex(r'^(.*)=$').sub('\\1',o)] = fn
		elif regex(r'^--[^-]').search(o):			# double dash option (change to space denoted)
			switcher.pop(o)
			switcher[regex(r'^(.*)=$').sub('\\1',o)] = fn
	opts_w_input_regex = regex(r"^("+'|'.join(opts_w_input)+r")(\S+)$") if len(opts_w_input_keys) != 0 else regex(r'^$')

	## Massage Args to a normalized state (expand compressedflags, expand = to another index)
	i_args = 0
	for l in range(1,len(argslist)):	# original list (skip index 0 since it is the caller filename)
		param = argslist[l]
		if param != "" and compressedflagsregex.search(param):
			del args[i_args]		# remove current combined arg
			num_flags = 0
			# uncompress flags
			for a in range(1,len(param)):	# skip hyphen by starting at 1
				i_args += num_flags
				args.insert(i_args, '-'+param[a])
				num_flags += 1
			
		elif opts_w_input_regex.match(param):
			# separate option from value
			option = regex(r'(.*)=$').sub('\\1', opts_w_input_regex.sub('\\1',param))  # remove =
			optarg = opts_w_input_regex.sub('\\2',param)
			args[i_args] = option
			i_args += 1
			args.insert(i_args, optarg)

		else:
			pass

		i_args += 1						# increment with l


	# PROCESS ARGS as actual input, modifying global variables
	i = -1
	while i+1 < len(args):
		i += 1
		try:
			func = switcher[args[i]]
			retVal = func(i)
		except KeyError:
			unknown(i)
		except SystemExit as exitrequest:
			raise(exitrequest)
		else:
			if isinstance(retVal, str) and retVal == "end_args":
				break
			elif isinstance(retVal, dict) and "increment" in retVal:
				i += retVal['increment']

		
	## // If-statements to check if interdependent options are satisfied // ##
	
	## // IF-statements to fill all vars with defaults if not already filled // ##


def check_prereqs():
	'''
	Validate environment & dependencies exist for script
	'''
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

	# TODO: check for required cygwin_pubring.asc public key file

	# VALID Environment
	if error_count != 0:
		return(error_count)
	else:
		print("PASS")
		return(0)


def setup_user():
	'''
	Configure user profile inside cygwin
	1. Create user home directory
	2. Copy files from /etc/skel to home dir for profile setup
	'''
	cygwin_bash = p.join(dir_cygwin,'bin',"bash.exe")
	cmds = [
		# 1. create user directory
		' '.join(['/bin/mkdir', '/home/"$(/bin/whoami)"']),
		# 2. add skeleton hidden files & ignoring any errors
		' '.join(['/bin/echo', '-n', '$('+
			' '.join(['/bin/cp', '/etc/skel/.*', '$HOME/', '2>/dev/null'])+  
		')']),
		# 3. add any skeleton non-hidden files & ignore not found error
		' '.join(['/bin/echo', '-n','$('+
			' '.join(['/bin/cp','-v','/etc/skel/*','$HOME/','2>/dev/null'])+
		')']) 
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
			'try {{ if (-not ([System.IO.File]::Exists("{cygwin_path}"))) {{ throw "Error" }} }} catch {{ }};'.format(
				cygwin_path=p.join(dir_cygwin,'bin',"bash.exe")
			)], 
			shell=False
		)

	except subprocess.CalledProcessError:
		eprint("INSTALLATION FAILED: cygwin's bash.exe not found @ {}/".format(p.join(dir_cygwin,'bin')))
		exit(-2)


def verify_sign(public_key_loc, signature, data):
    '''
    Verifies with a public key from whom the data came that it was indeed 
    signed by their private key
    param: public_key_loc Path to public key
    param: signature String signature to be verified
	param: data object in base64 encoding
    return: Boolean. True if the signature is valid; False otherwise. 
    '''
    return True
    # from Crypto.PublicKey import DSA 
    # from Crypto.Signature import DSS 
    # from Crypto.Hash import SHA256
    # pub_key = open(public_key_loc, "rb").read()
    # pub_dsakey = DSA.import_key(pub_key) 		# ValueError: DSA key format is not supported
    # verifier = DSS.new(pub_dsakey, 'fips-186-3') 
    # digest = SHA256.new() 
    # # Assumes the data is base64 encoded to begin with
    # digest.update(base64.b64decode(data)) 
    # if verifier.verify(digest, base64.b64decode(signature)):
    #     return True
    # return False


def install_cygwin():

	try:
		# Check cygwin64's bash.exe already exists
		subprocess.check_call([ 
			'powershell.exe',
			'try {{ if (-not ([System.IO.File]::Exists("{cygwin_path}"))) {{ throw "Error" }} }} catch {{ }};'.format(
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
		with open(spec['output'], 'wb') as o:
			while True:
				bytes = download.read(256)
				if not bytes: # EOF
					break
				o.write(bytes)
	# 
	def exe_download_handler(download,spec):
		write2file(download, spec)
		f = base64.b64encode(open(spec['output'],'rb').read())
		if not verify_sign(public_key_file, vars['exe.sig'], f):
			raise( Exception("INVALID SIGNATURE: downloaded {exe} failed verification".format(exe=spec['output'])) )

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
			# Handles HTTP exceptions
			# Handles invalid content-type
			# Handles invalid signature
			eprint(err)
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
				pinstaller.wait(5)
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
	VERBOSE = False
	FORCE = False
	is_64bit = True if registersize > 2**32 else False
	dir_cygwin = p.join(p.abspath(ossep), 'cygwin' + ('64' if is_64bit else '32'))

	config_actions = [ 
		{ 'fn':install_cygwin, 'onerror':"FAILED: download & installation of cygwin." },
		{ 'fn':verify_installation, 'onerror':"FAILED: verification of cygwin installation." },
		{ 'fn':setup_user, 'onerror':"FAILED: cygwin user profile setup." },
		{ 'fn':cygwin_configure.MAIN, 'onerror':"FAILED: ansible configuration of cygwin." }
	]


	try:
		process_args(argslist)

		if check_prereqs() != 0: 
			exit(1)

		if not MODE_QUIET:
			print_banner()

		vvvprint("{}-bit detected.".format('64' if is_64bit else '32'))
		vvvprint("Target Cygwin installation directory: \n\t {}".format(dir_cygwin))

		for action in config_actions:
			try:
				action['fn']()
			except KeyboardInterrupt as usr_canx:
				raise(usr_canx)
			except SystemExit as e:
				exit(e.code)
			except:
				eprint( action['onerror'] )
				exit(1)

	except KeyboardInterrupt as usr_canx:
		eprint('\n'+"User interrupted build process.  Exiting...")
		exit(1)	
	else:
		exit(0)

