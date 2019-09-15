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
	gcloud config set project "rainfall-estimation"
	gcloud config set compute/zone "us-central1-a"
	
	# Check if cluster exists and isn't running a current instance
	CLUSTER=""
	if [ -n "$(gcloud compute instances list | grep high-cpu-cluster)" ]; then
		CLUSTER=true
		if [ -n "$(kubectl get pods | grep "rainfall-predictor" )" ]; then
			# there is a current deployment running
		fi
	fi

	if [ ! $CLUSTER ]; then
		# Build cluster
		gcloud beta container clusters create "high-cpu-cluster-1" \
			--zone "us-central1-a" \
			--cluster-version "1.13.7-gke.8" \
			--num-nodes "1" \
			--machine-type "n1-highcpu-4" \
			--image-type "COS" \
			--disk-type "pd-standard" \
			--disk-size "20" \
			--metadata disable-legacy-endpoints=true \
			--scopes "https://www.googleapis.com/auth/devstorage.read_write",\
					"https://www.googleapis.com/auth/logging.write",\
					"https://www.googleapis.com/auth/monitoring",\
					"https://www.googleapis.com/auth/servicecontrol",\
					"https://www.googleapis.com/auth/service.management.readonly",\
					"https://www.googleapis.com/auth/trace.append" \
			--enable-cloud-logging \
			--enable-cloud-monitoring \
			--enable-ip-alias \
			--network "projects/rainfall-estimation/global/networks/default" \
			--subnetwork "projects/rainfall-estimation/regions/us-central1/subnetworks/default" \
			--default-max-pods-per-node "110" \
			--addons HorizontalPodAutoscaling \
			--no-enable-basic-auth \
			--no-enable-autoupgrade \
			--enable-autorepair \
			--resource-usage-bigquery-dataset "usage_metering_dataset" \
			--enable-network-egress-metering \
			--enable-resource-consumption-metering
		
		# Verify instance ready?
		# $(gcloud compute instances list)
	fi


	# Add Persistent Storage to cluster
	# kubectl apply -f "$DIRNAME/scripts/rainfall-volumeclaim.yaml"
	# kubectl get pvc
	# STORAGE_PARTITION_SUCCESS="$?"


	# run kubectl deployment command on new container image
	# kubectl create -f "$DIRNAME/scripts/rainfall.yaml"
	# kubectl get pod -l app=rainfall-predictor
	# DEPLOYMENT_SUCCESS="$?"




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
