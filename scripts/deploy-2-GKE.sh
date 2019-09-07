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
	# command -v docker >/dev/null 2>&1 || { ((missing_prereqs++)); echo >&2 "MISSING PREREQ: docker is not installed but is required."; }
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

deploy() {

}

## Main Loop ##
main() {
	$MODE_QUIET && 1>/dev/null;
	print_banner 1>&1;

	# set gcloud configuration settings

	# Check if cluster exists and isn't running a current instance

	# Build cluster

	# run release?  increment Version and push tag to git source control?

	# tag image with $REPO = gcr.io/$IMAGE_NAME:$VERSION

	# verify gcloud auth configure-docker has been run once for the very first time?
	# docker push image to Google Container Registry

	# run kubectl deployment command on new container image






	# if [ ! -d "$DIRNAME/$BUILD_DIR" ]; then
	# 	if [ $VERBOSE ]; then
	# 		echo "Creating Directories: "
	# 		echo -n "  " && echo "$DIRNAME/$BUILD_DIR"	# macosx mkdir -p -v [path] fails, is official bug
	# 	fi
	# 	mkdir -p "$DIRNAME/$BUILD_DIR"

	# elif [ -n "$(ls -al "$DIRNAME/$BUILD_DIR" | egrep --invert-match '^(.*[ ]((\.)|(\.\.))$)|(total.*$)')" ]; then
	# 	## CLEAN PREVIOUS TEST BUILD
	# 	echo "cleaning...";
	# 	if [ $VERBOSE == true ]; then
	# 		rm -vfR "$DIRNAME/$BUILD_DIR"/*
	# 	else
	# 		rm -fR "$DIRNAME/$BUILD_DIR"/*
	# 	fi
	# 	echo "clean complete.";
	# fi
	
	# ## BUILD
	# build 1>&1;

	# if [[ $ERROR_COUNT > 0 ]]; then
	# 	echo "Python App build completed but with $ERROR_COUNT error(s)." && echo;
	# 	exit 1;
	# else 
	# 	echo "Python App build complete." && echo;
	# fi
}

# ---------------------------
# CODE START - Ingest line args
# ---------------------------
process_args "$@";

check_prereqs || exit 1;

main                    # Run Main Loop
exit 0;
