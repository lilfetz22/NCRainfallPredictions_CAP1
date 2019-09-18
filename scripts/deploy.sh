#!/bin/bash
#
# FILE: deploy.sh
#=========================================
# Deploys App Container to Environment
# Docker Container located in /bin
#
# Usage:
#	$> ./deploy.sh [options]
# 
# For Options, see help
#   $> ./deploy.sh --help
#=========================================

DIRNAME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd )" && DIRNAME="${DIRNAME%/scripts}";
SCRIPT_FILE=""
NAME="rainfall"
PROJECT_ID="rainfall-estimation"

usage() {
	echo "Usage: ./$(basename "$0") <ENV> <passthru_args>" 1>&2; exit 1;
}
help() {
    echo ""
    echo " Rainfall Estimation Deployment "
    echo "--------------------------------"
    echo "This script is a passthrough to multiple possible deployment"
	echo "environments.";
    usage | echo;
    echo ""
    echo "Configured Environments (ENV): "
    echo "  GKE    Google Kubernetes Environment"
    echo ""
    exit 0;
}

# Process line arguments
process_args() {
	case "$1" in		   # process & check 1st command line arg
		-h|--help)
			help
			;;
		GKE)
			SCRIPT_FILE="$DIRNAME/scripts/deploy-2-GKE.sh"
			REPO="gcr.io"
			;;
		--)			# End of all options.
			;;
		-?*)		#Unknown option
			usage;
			;;
		*)			# Default: no more options
	esac
	shift
	
	[ -z "$SCRIPT_FILE" ] && echo "MISSING PARAM: no Environment provided. Aborting..." >&2 && exit 1;
	
}

deploy() {

	# Bump version
	"$DIRNAME/scripts/bump-version.py" "minor"
	VERSION="v$(cat "$DIRNAME/VERSION")"
	# Due to version bump, run dockerify to update image with VERSION file
	"$DIRNAME/scripts/dockerify.sh" --quiet --no-rebuild --keep-version 
	# Create Release tag in git
	# if branch == master?
	# git add VERSION
	# git commit -m "Version: $VERSION"
	# git tag -a "$VERSION" -m "Version: $VERSION"
	# git push
	# git push --tags

	# tag image with $REPO = gcr.io/$IMAGE_NAME:$VERSION
	# Tag docker file with new version, run dockerify if necessary
	docker tag "$NAME:latest" "$REPO/$PROJECT_ID/$NAME:$VERSION"


	# verify gcloud auth configure-docker has been run once for the very first time?
	# docker push image to Google Container Registry

	# Upload docker image to container registry ($REPO)
	# temp_file=$(mktemp)
	# exec 3 < "$temp_file"
	# trap 'rm "$temp_file"' SIGTERM SIGERR
	docker push "$REPO/$PROJECT_ID/$NAME:$VERSION" 2>&1 1>&3 &
	# pid_upload=$!
	# wait $pid_upload
	# exit_status="$?"
	# output=$(cat <&3)
	# if [ $exit_status != 0 ]; then
		# echo "$output"
		# if [ -n "$(echo "$output" | grep 'unauthorized')" ]; then
		#	echo "POSSIBLE FIX: run \`$> gcloud auth configure-docker\`" 
		# fi
	# 	exit $exit_status;
	# fi

	# Run deployment operations
	. "$SCRIPT_FILE" "$@"
}

keep_awake() {
	if [[ "$OSTYPE" == "linux-gnu" ]]; then
		# disable sleep, set TRAP to re-enable sleep capability, execute script
		targets="sleep.target suspend.target hibernate.target hybrid-sleep.target"
		sudo systemctl mask $targets
		trap "sudo systemctl unmask $targets" ERR EXIT
		$1	# run intended script/function
		return "$?"

	elif [[ "$OSTYPE" == "darwin"* ]]; then		# Mac OSX
		$1 &
		pid=$!
		caffeinate -i -w $pid
		wait $pid
		exit_status="$?"
		[ $exit_status != 0 ] && exit $exit_status;
		return 

	# elif [[ "$OSTYPE" == "cygwin" ]]; then		# POSIX compatibility layer and linux env emulation for windows
	# elif [[ "$OSTYPE" == "msys" ]]; then		# lightweight shell and GNU utilities for Windows (part of MinGW)
	# elif [[ "$OSTYPE" == "win32" ]]; then		# maybe windows
	# elif [[ "$OSTYPE" == "freebsd"* ]]; then	# FreeBSD
	# else
		# Unknown
	fi

	# FALL THROUGH default
	$1		# run like normal
}

# ---------------------------
# CODE START - Ingest line args
# ---------------------------
process_args "$@";

keep_awake deploy
exit 0;
