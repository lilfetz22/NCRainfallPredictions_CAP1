#!/bin/bash
#
# FILE: deploy-2-GKE.sh
#=========================================
# Deploys App Container to Google Kubernetes Environment
# Docker Container located in /bin
#
# Usage:
#	$> ./deploy-2-GKE.sh [options]
# 
# For Options, see help
#   $> ./deploy-2-GKE.sh --help
#=========================================

# DEFAULT VARS (accepts environment variables)
[ -z "$DIRNAME" ] && DIRNAME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd )" && DIRNAME="${DIRNAME%/scripts}";
# [ -z "$BUILD_DIR" ] && BUILD_DIR="build"
[ -z "$VERBOSE" ] && VERBOSE=false

usage() {
	echo "Usage: ./$(basename "$0") [[-q | --quiet][-v |--verbose]] [-h | --help]" 1>&2; exit 1;
}
help() {
    echo ""
    echo " Rainfall Estimation Deploy Script "
    echo "-----------------------------------"
    # echo "Automated app build script.  Jupyter notebooks are converted to regular python files." \
    # 	 "Built files are located in the ${DIRNAME%/}/$BUILD_DIR directory."
    echo ""
    usage | echo;
    echo "Available Options: "
    echo "  -h | --help   Help"
	echo "  -q | --quiet  Execute quietly except for errors"
	echo "  -v | --verbose   Show more in-depth log output, unless -q is enabled"
    echo ""
    echo "ENVIRONMENT VARS:"
    # echo "  DIRNAME, BUILD_DIR, VERBOSE"
    echo ""
    exit 0;
}
print_banner() {
	echo "";
    echo "============================================";
    echo "|   Rainfall Estimation Deployment (GKE)   |";
    echo "============================================";
	echo "";
}

check_prereqs() {
	missing_prereqs=0
	command -v gcloud >/dev/null 2>&1 || { ((missing_prereqs++)); echo >&2 "MISSING PREREQ: gcloud is not installed but is required."; }
	command -v kubectl >/dev/null 2>&1 || { ((missing_prereqs++)); echo >&2 "MISSING PREREQ: kubectl is not installed but is required."; }
	# List additional prereqs here
	return "$missing_prereqs"
}

# timestamp function in ms
timestamp() {
  date +"%s"
}

# Process line arguments
process_args() {
	while :; do
		case "$1" in		   # process & check command line options
			-h|--help)
				help
				;;
			-q|--quiet)
				MODE_QUIET=true
				;;
			-v|--verbose)
				VERBOSE=true
				;;
			--)			# End of all options.
				shift
				break
				;;
			-?*)		#Unknown option
				usage;
				;;
			*)			# Default: no more options, break out of loop.
				break
		esac
		
		shift
	done
		
	## // If-statements to check if interdependent options are satisfied // ##
	
	## // IF-statements to fill all vars with defaults if not already filled // ##
	[ -z "$MODE_QUIET" ] && MODE_QUIET=false
}

prepare_yaml() {
	[ -z "$1" ] && echo "ERROR: template.yaml filename must be provided." && exit 1

	template="${1}"			# ARG #1 : filename of template yaml
	finalYAML=$(mktemp)		# make temporary file

	generated_stdin_cmds="$(echo "cat <<EOF >\"$finalYAML\""; cat $template; echo EOF;)"
	source /dev/stdin <<<"$generated_stdin_cmds"
	echo "$finalYAML";		# return filepath of filled-in file
	return 0
}

deploy() {

	DEPLOYMENT_FILE="$(prepare_yaml "$DIRNAME/scripts/$NAME.yaml")"
	# DEPLOYMENT_FILE="$(prepare_yaml "$DIRNAME/scripts/$NAME.tpl.yaml")"
	trap 'rm "$DEPLOYMENT_FILE"' ERR EXIT SIGTERM

	# run kubectl deployment command on new container image
	kubectl create -f "$DEPLOYMENT_FILE"
	DEPLOYMENT_SUCCESS="$?"
	if [ "$DEPLOYMENT_SUCCESS" != 0 ]; then
		echo >&2 "Error during kubectl create. Exiting...";
		exit $DEPLOYMENT_SUCCESS;
	else
		echo "App deployment initiated..."
		ALL_RUNNING=false
		COUNTER=0
		kube_CMD="kubectl get pod -l app=$NAME-predictor"
		while [ $ALL_RUNNING = false ]; do
			sleep 2s
			COUNTER=$((COUNTER+2))
			if [ $((COUNTER % 10)) == 0 ]; then
				## kube get pods | awkfilter_getstatus | awkfilter_getnotrunning as an array
				POD_STATUS=(\
							$($kube_CMD \
							  | awk -F "[ ][ ]+" 'NR>=2 {print $3}' \
							  | awk 'toupper($0) !~ /^RUNNING$/ { print }'\
						     )\
						   )
				if [ ${#POD_STATUS[@]} == 0 ]; then
					ALL_RUNNING=true
					echo && echo "Verified all pods are running."
					break
				fi
			fi
			[ $((COUNTER % 6)) == 0 ] && echo "." || echo -n "."
			[ $COUNTER -gt 180 ] && echo && echo "Start time exceeded 3 minutes. Please check for errors. Exiting..." && exit 3
		done
		return 0;
	fi
}

## Main Loop ##
main() {
	$MODE_QUIET && 1>/dev/null;
	# if [ ""  ]; then
		print_banner 1>&1;
	# fi

	# set gcloud configuration settings
	gcloud config set project "rainfall-estimation"
	gcloud config set compute/zone "us-central1-a"
	
	## Create Cluster (if necessary)
	. "$DIRNAME/scripts/GKE-cluster-create.sh" "high-cpu-cluster-1" 
	[ "$?" != 0 ] && exit 1

	deploy
	echo "App deployment to GKE complete." && echo;
}

# ---------------------------
# CODE START - Ingest line args
# ---------------------------
process_args "$@";

check_prereqs || exit 1;

main                    # Run Main Loop
