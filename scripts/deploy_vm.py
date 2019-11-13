#!/usr/bin/env python3
#
# FILE: deploy_vm.py
#=========================================
# Google Compute Engine VM build & deploy script.
#
# Usage:
#	$> ./deploy_vm.py [options]
# 
# For Options, see help
#   $> ./deploy_vm.py --help
#=========================================
from __future__ import print_function
import sys, os, platform
import glob
import re
import json
import copy
import mmap
import subprocess
import time
import datetime
from pytz import timezone
from build import build as Builder
from bumpversion import bump


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, flush=True, **kwargs)

def usage(printTo=""):
	this_file = os.path.basename(os.path.abspath(__file__))
	printFn = print if printTo == "stdout" else eprint
	printFn("Usage: ./{0} [-q | --quiet] [--no-autostart] [-r <type> | --release=<type>]".format(this_file))
	printFn("       ./{0} [-q | --quiet] [--no-rebuild] [--keep-version]".format(this_file))
	printFn("       ./{0} [--destroy]".format(this_file))
	printFn("       ./{0} [-h | --help]".format(this_file))
	exit(1)

def help():
    print("")
    print(" Rainfall Predictor VM Creation Script ")
    print("---------------------------------------")
    print("Google Compute Engine VM build & deploy script.  Ansible provisions a GCE instance" \
		 +"with a persistent disk, static IP, and Debian OS.  Once created, Ansible installs" \
		 +"the required app dependencies, configures the OS, and installs the app as a service" \
		 +"named {0}.service. ".format(NAME) \
		 +"Autostart of the service is the default but can be" \
		 +"toggled off with the provided option flag.  Login information will be provided after" \
		 +"build and deploy succeeds.  Reverse & clean resources by running with the --destroy flag")
    print("")
    try: 
        usage(printTo="stdout")
    except SystemExit:
        print("")
    print("Available Options: ")
    print("  -h | --help     Help")
    print("  -q | --quiet    Execute quietly except for errors")
    print("  -r <type> | --release=<type>   Type of release either Major, Minor, or Update")
    print("                     DEFAULT: Minor, update version number only")
    print("  --destroy       Removes a deployed VM and releases GCE resouces")
    print("  --no-autostart  Complete ansible build except for autorun of service")
    print("  --no-rebuild    Makes container with current ./build files, fails if empty")
    print("  --keep-version  Does not increment version number update field 1.1.X")
    print("")
    print("DEFAULT VARS:")
    print("  BUILD_DIR: {}".format(os.path.join(os.path.basename(DIRNAME),BUILD_DIR)))
    print("")
    # print("ENVIRONMENT VARS:")
    # print("  DIRNAME, BUILD_DIR, VERBOSE")
    # print("")
    exit(0)

def print_banner():
    print('\n'+ \
			"=========================================")
    print(	"|   VM Builder for Rainfall Predictor   |")
    print(  "=========================================")
    print(  "START: {}".format(datetime.datetime.now(timezone('US/Eastern')).strftime("%a %b %d %H:%M:%S %Z %Y"))+'\n')

def check_prereqs():
	missing_prereqs = 0
	prereqs = []
	if os_version == 'Windows':
		prereqs = [
			{ 'test' : ["powershell.exe", "Get-Command ansible 2>&1 | out-null"], 'isshell':False, 'onerror': "ansible is not installed but is required." }
		]
	elif os_version == 'Linux' or os_version == 'Darwin':
		prereqs = [
			{ 'test' : ["command", "-v", "ansible"], 'isshell':True, 'onerror': "ansible is not installed but is required." }
		]
	else:
		eprint("Platform ({}) not supported".format(os_version))
		exit(3)

	for prereq in prereqs:
		try:
			subprocess.check_call(prereq['test'], shell=prereq['isshell'])
		except subprocess.CalledProcessError:
			missing_prereqs += 1
			eprint("MISSING PREREQ: {}".format(prereq['onerror']))
		else:
			continue  # command found, check next prereq


	## Non-application based dependencies
	secretsfile = os.path.join("scripts","ansible","roles","configure","vars","secrets.yml")
	if os.path.isfile(secretsfile):
		# Check for required fields
		with open(secretsfile, 'rb', 0) as fsecrets, \
		  mmap.mmap(fsecrets.fileno(), 0, access=mmap.ACCESS_READ) as s:
			if not re.search(br'^admin_secret: \S+$', s, re.MULTILINE):
				missing_prereqs += 1
				eprint("PREREQ ERROR: secrets.yml file must match syntax 'admin_secret: password' (no quotes).")
		
	else:
		missing_prereqs += 1
		eprint("MISSING PREREQ: {} file missing.".format(
			os.path.join(os.path.basename(DIRNAME), secretsfile)
		))

	return(missing_prereqs)

# timestamp function in ms
def timestamp():
	return(round(datetime.datetime.now().timestamp(), 0))


# Process line arguments
def process_args( argslist ):
	global MODE_QUIET, DESTROY, AUTOSTART, REBUILD, BUMP_VERSION, BUMP_VER_SIZE, RELEASE_TYPE
	args = copy.copy(argslist)

	# Argument Handlers
	def request_help(i):
		help()
	def set_quiet(i):
		global MODE_QUIET
		MODE_QUIET = True
	def set_releasetype(i):
		global RELEASE_TYPE
		optarg = args[i+1]
		if re.search(r'^(major|minor|update)$', optarg, re.IGNORECASE):
			RELEASE_TYPE = optarg
			return({ 'increment': 1 })		# hop over optarg
		else:
			usage()
	def toggleDestroy(i):
		global DESTROY
		DESTROY = True
	def turnoff_autostart(i):
		global AUTOSTART
		AUTOSTART = False
	def turnoff_rebuild(i):
		global REBUILD
		REBUILD = False
	def turnoff_v_bump(i):
		global BUMP_VERSION
		BUMP_VERSION = False
	# def set_verbose(i):
	# 	global VERBOSE
	# 	VERBOSE = True
	def end_args(i):
		return("end_args")
	def unknown(i):
		usage()
	
	## equals denote has additional input parameter
	switcher = {
		'-h'        : request_help,
		'--help'    : request_help,
		'-q'        : set_quiet,
		'--quiet'   : set_quiet,
		'-r='		: set_releasetype,
		'--release=': set_releasetype,
		'--destroy' : toggleDestroy,
		'--no-autostart' : turnoff_autostart,
		'--no-rebuild'   : turnoff_rebuild,
		'--keep-version' : turnoff_v_bump,
		# '-v'        : set_verbose,
		# '--verbose' : set_verbose,
		'--' : 		  end_args
	}

	# Dynamically finds other alternatives from spec ^
	compressedflags = list(filter(lambda opt: re.search(r'^-[^-][^=]*$', opt), switcher.keys()))
	compressedflags = [re.sub(r'^-(.*)$', '\\1', i) for i in compressedflags]		# removes the hyphen
	if len(compressedflags) > 1:
		compressedflagsregex = re.compile("^-["+''.join(compressedflags)+"]{2,"+str(len(compressedflags))+"}$")
	else:
		compressedflagsregex = re.compile("^$")		# almost impossible to match 

	opts_w_input = dict(filter(lambda item: re.search(r'=$', item[0]), switcher.items()))
	opts_w_input_keys = list(opts_w_input.keys())
	for o in opts_w_input_keys:			# Fixes switcher so keys will be found
		fn = opts_w_input[o]
		if re.search(r'^-[^-]', o):				# single dash option (remove =)
			opts_w_input.pop(o)
			switcher.pop(o)
			switcher[re.sub(r'^(.*)=$', '\\1',o)] = fn
		elif re.search(r'^--[^-]', o):			# double dash option (change to space denoted)
			switcher.pop(o)
			switcher[re.sub(r'^(.*)=$', '\\1',o)] = fn
	opts_w_input_regex = re.compile(r"^("+'|'.join(opts_w_input)+r")(\S+)$")

	## Massage Args to a normalized state (expand compressedflags, expand = to another index)
	i_args = 1
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
			option = re.sub(r'(.*)=$','\\1', opts_w_input_regex.sub('\\1',param))  # remove =
			optarg = opts_w_input_regex.sub('\\2',param)
			args[i_args] = option
			i_args += 1
			args.insert(i_args, optarg)

		else:
			pass

		i_args += 1						# increment with l


	i = 0		# skip index 0 since it is the filename not an parameter
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
	if RELEASE_TYPE is not None:
		BUMP_VERSION = True
		BUMP_VER_SIZE = "{}".format(RELEASE_TYPE)	

	## // IF-statements to fill all vars with defaults if not already filled // ##
	AUTOSTART = AUTOSTART if AUTOSTART is not None else True
	DESTROY = DESTROY if DESTROY is not None else False
	REBUILD = REBUILD if REBUILD is not None else True
	BUMP_VERSION = BUMP_VERSION if BUMP_VERSION is not None else True
	BUMP_VER_SIZE = BUMP_VER_SIZE if BUMP_VER_SIZE is not None else "minor"
	MODE_QUIET = MODE_QUIET if MODE_QUIET is not None else False	


def deploy():
	if MODE_QUIET == True:
		sys.stdout = open(os.devnull, 'w')

	SCRIPT_STARTS = timestamp()

	if DESTROY == True:
		ANSIBLE_CONFIG = os.path.join(DIRNAME,"scripts","ansible","ansible.cfg")
		PLAYBOOK_FILE = os.path.join(DIRNAME,"scripts","ansible","cleanup.yml")
		ENV_VARS = "ANSIBLE_CONFIG={}".format(ANSIBLE_CONFIG)

		if os_version == 'Windows':
			eprint("Windows is not yet supported")
			raise(Exception())
			# Add env variables in Powershell?
			# ext_cmd = [ 
			# 	'powershell.exe',
			# 	'{0} ansible-playbook "{1}"'.format(ENV_VARS,PLAYBOOK_FILE)
			# ]
			# is_shellcmd = False

		elif os_version == 'Linux' or os_version == 'Darwin':
			# /bin/bash -c "$ENV_VARS ansible-playbook $DIRNAME/scripts/ansible/cleanup.yml" &
			ext_cmd = [
				'{0} ansible-playbook {1}'.format(ENV_VARS,PLAYBOOK_FILE)
			]
			is_shellcmd = True

		else:
			eprint("Platform ({}) not supported".format(os_version))
			exit(3)

		## RUN external subprocess
		print("[VM DESTROY] $> "+" ".join(ext_cmd))
		try:
			p = subprocess.Popen(
				ext_cmd,
				shell=is_shellcmd,
				stdout=subprocess.PIPE,
				stderr=subprocess.STDOUT
			)
			for line in p.stdout.readlines():
				print(line)
			exit_status = p.wait()

			## Handle Ansible build status 
			if exit_status != 0:
				raise( Exception() )

		except KeyboardInterrupt as usr_canx:
			raise(usr_canx)
			# ansiblePID=$!
			# trap "ps -p $ansiblePID > /dev/null && kill $ansiblePID" ERR EXIT
			# wait $ansiblePID
		except:
			eprint("[VM DESTROY] Error occured.  Aborting..."+'\n')
			exit(1)
		else:
			SCRIPT_STOPS = timestamp()
			print("[VM DESTROY] Total Execution Time: {} seconds".format(SCRIPT_STOPS-SCRIPT_STARTS)+'\n')
			print("Google Cloud Resources Summary: ")
			print("------------------------------- ")
			print("   Compute Instance: RELEASED")
			print("   Static IP: RELEASED")
			print("   Persistent Data Disk: 1 Resource Allocated ($)"+'\n')
			exit(0)
	## ENDIF  DESTROY


	if REBUILD == True:
		# ensure build files are up to date
		print("[VM BUILD] Running code build script...")
		BUILD_SCRIPT_STARTS = timestamp()
		try:
			# Set env vars??
			Builder.build()
		except:
			eprint("[VM BUILD] build failed. Aborting..."+'\n')
			exit(1)
		else:
			BUILD_SCRIPT_STOPS = timestamp()
			print("[VM BUILD] Code Build completed! ({} seconds)".format(BUILD_SCRIPT_STOPS-BUILD_SCRIPT_STARTS)+'\n')

	elif len(os.listdir(os.path.join(DIRNAME,BUILD_DIR))) == 0:
		# build folder is empty
		eprint("MISSING FILES: build directory is empty."+'\n')
		exit(1)

	else:
		pass
	## ENDIF BUILD


	if BUMP_VERSION == True:
		try:
			bump(BUMP_VER_SIZE)
		except:
			eprint("[VM BUILD] Error occured. Aborting..."+'\n')
			exit(1)
		else:
			print("")
			time.sleep(2)	# Dramatic effect (seconds)
	## ENDIF Version Bump


	print("[APP_DEPLOY] Deploying application to Google Cloud Compute Instance...")
	# ansible build [ host_ips, deployment YAML ]
	# Parameters
	ANSIBLE_CONFIG = os.path.join(DIRNAME,"scripts","ansible","ansible.cfg")
	DEPLOYMENT_FILE = os.path.join(DIRNAME,"scripts","ansible","deploy-app-vm.yml")
	print("[APP_DEPLOY] Set ANSIBLE_CONFIG={}".format(ANSIBLE_CONFIG))
	print("[APP_DEPLOY] Set DEPLOYMENT_FILE={}".format(DEPLOYMENT_FILE))
	PLAYBOOK_VARS = {
		"local_project_dir": DIRNAME
	}
	if AUTOSTART == False:
		PLAYBOOK_VARS['app_autostart'] = False
  
	# combine any vars into ansible variable string
	EXTRA_VARS = "" if not bool(PLAYBOOK_VARS) \
		            else "--extra-vars {}".format(json.dumps(PLAYBOOK_VARS, separators=(',', ':')))

	# Set to shell environmental variable formatting
	ENV_VARS = "ANSIBLE_CONFIG={}".format(ANSIBLE_CONFIG)

	if os_version == 'Windows':
		eprint("Windows is not yet supported")
		raise(Exception())
		# Add env variables in Powershell?
		# ext_cmd = [ 
		# 	'powershell.exe',
		# 	'{0} ansible-playbook {1} "{2}"'.format(ENV_VARS,EXTRA_VARS,DEPLOYMENT_FILE)
		# ]
		# is_shellcmd = False

	elif os_version == 'Linux' or os_version == 'Darwin':
		# /bin/bash -c "$ENV_VARS ansible-playbook $EXTRA_VARS $DIRNAME/scripts/ansible/deploy-app-vm.yml" &
		ext_cmd = [
			"{0} ansible-playbook {1} {2}".format(ENV_VARS,EXTRA_VARS,DEPLOYMENT_FILE)
		]
		is_shellcmd = True

	else:
		eprint("Platform ({}) not supported".format(os_version))
		exit(3)

	## RUN external subprocess
	ANSIBLE_BUILD_STARTS = timestamp()
	print("[APP_DEPLOY] $> "+" ".join(ext_cmd))
	try:
		p = subprocess.Popen(
			ext_cmd,
			shell=is_shellcmd,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT
		)
		for line in p.stdout.readlines():
			print(line)
		exit_status = p.wait()

		## Handle Ansible build status 
		if exit_status != 0:
			raise( Exception() )

	except KeyboardInterrupt as usr_canx:
		raise(usr_canx)
			# ansiblePID=$!
			# trap "ps -p $ansiblePID > /dev/null && kill $ansiblePID" ERR EXIT
			# wait $ansiblePID
	except:
		eprint("[VM BUILD] Error occured.  Aborting..."+'\n')
		exit(2)
	else:
		ANSIBLE_BUILD_STOPS = timestamp()

	print('\n'+"[VM BUILD] GCE VM deployed in {} seconds.".format(ANSIBLE_BUILD_STOPS-ANSIBLE_BUILD_STARTS))

	SCRIPT_STOPS = timestamp()
	print("[VM BUILD] Total Execution Time: {} seconds".format(SCRIPT_STOPS-SCRIPT_STARTS)+'\n')
	# Instructions
	print("  APP STATUS  ")
	print(" ------------ ")
	print("SERVICE={}.service".format(NAME))
	print("APP={}".format('RUNNING' if AUTOSTART == True else 'INSTALLED'))
	print("TO CONNECT:")
	print("     $> ssh -i ~/.ssh/srvacct-gce sa_117909082819485756837@ip")
	print("     --or--")
	print("     $> open http://ip")
	print("")


def keep_awake(caffeinatedFn):

	if os_version == 'Linux':
		pass
		# disable sleep, set TRAP to re-enable sleep capability, execute script
		# targets="sleep.target suspend.target hibernate.target hybrid-sleep.target"
		# sudo systemctl mask $targets
		# trap "sudo systemctl unmask $targets" ERR EXIT
		# $1	# run intended script/function
		# return "$?"

	elif os_version == 'Darwin':
		pass
		# $1 &
		# pid=$!
		# trap "ps -p $pid > /dev/null && kill $pid" ERR EXIT
		# caffeinate -i -w $pid
		# wait $pid
		# exit_status="$?"
		# [ $exit_status != 0 ] && exit $exit_status;
		# return 
		
	elif os_version == 'Windows':
		pass
		
	else:
		pass	# Unknown

	# FALL THROUGH default
	caffeinatedFn()		# run like normal



# ------------------------------
# CODE START - Ingest line args
# ------------------------------
if __name__ == "__main__":
	# DEFAULT VARS (accepts environment variables)
	DIRNAME = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))		# cd ../..
	BUILD_DIR = "build"
	AUTOSTART = None
	DESTROY = None
	MODE_QUIET = None
	REBUILD = None
	BUMP_VERSION = None
	BUMP_VER_SIZE = None
	RELEASE_TYPE = None
	error_count = 0		# prevent evironment pollution
	os_version = platform.system()

	NAME="rainfall-predictor"

	try:
		process_args(sys.argv)

		if check_prereqs() != 0: 
			exit(1)

		if not MODE_QUIET:
			print_banner()

		keep_awake(deploy)

	except KeyboardInterrupt as usr_canx:
		eprint('\n'+"User interrupted deploy process.  Exiting...")
		exit(1)	
	else:
		exit(0)
