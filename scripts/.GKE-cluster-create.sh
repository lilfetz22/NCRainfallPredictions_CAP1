#!/bin/bash
#
# FILE: .GKE-cluster-create.sh
#=========================================
# Creates cluster on Google Cloud running Kubernetes
# has specific CPU count and RAM allocation type
#
# Usage:
#	$> ./.GKE-cluster-create.sh [options]
# 
# For Options, see help
#   $> ./.GKE-cluster-create.sh --help
#=========================================

# DEFAULT VARS (accepts environment variables)
[ -z "$DIRNAME" ] && DIRNAME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd )" && DIRNAME="${DIRNAME%/scripts}";
[ -z "$VERBOSE" ] && VERBOSE=false

usage() {
	echo >&2 "Usage: ./$(basename "${BASH_SOURCE[0]}") [options] <cluster_name>"
	echo >&2 "       ./$(basename "${BASH_SOURCE[0]}") [-q | --quiet] <cluster_name>";
	echo >&2 "       ./$(basename "${BASH_SOURCE[0]}") [-v | --verbose] <cluster_name>";
	echo >&2 "       ./$(basename "${BASH_SOURCE[0]}") [-h | --help]"; 
	exit 1;
}
help() {
    echo ""
    echo " Google Kubernetes Cluster Creation "
    echo "------------------------------------"
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
    echo "===============================";
    echo "|   Cluster Creation on GKE   |";
    echo "===============================";
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
				[ -n "$1" ] && CLUSTER_NAME="$1"
				break
				;;
			-?*)		#Unknown option
				usage;
				;;
			*)			# Default: Last parameter not an option, break out of loop.
				[ -n "$1" ] && CLUSTER_NAME="$1"
				break
		esac
		
		shift
	done
		
	## // If-statements to check if interdependent options are satisfied // ##
	
	## // IF-statements to fill all vars with defaults if not already filled // ##
	[ -z "$CLUSTER_NAME" ] && CLUSTER_NAME=""
	[ -z "$MODE_QUIET" ] && MODE_QUIET=false
}

create_cluster() {
	
	# Build cluster
	echo "Creating cluster '$CLUSTER_NAME' on Google's Kubernetes Environment..."

	gcloud beta container clusters create "$CLUSTER_NAME" \
		--release-channel "regular" \
		--num-nodes "1" \
		--machine-type "n1-highcpu-4" \
		--image-type "COS" \
		--disk-type "pd-standard" \
		--disk-size "20" \
		--metadata disable-legacy-endpoints=true \
		--scopes "https://www.googleapis.com/auth/devstorage.read_write","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" \
		--enable-cloud-logging \
		--enable-cloud-monitoring \
		--enable-ip-alias \
		--network "projects/rainfall-estimation/global/networks/default" \
		--subnetwork "projects/rainfall-estimation/regions/us-central1/subnetworks/default" \
		--default-max-pods-per-node "110" \
		--addons HorizontalPodAutoscaling \
		--no-enable-basic-auth \
		--enable-autorepair \
		--resource-usage-bigquery-dataset "usage_metering_dataset" \
		--enable-network-egress-metering \
		--enable-resource-consumption-metering
		# --no-enable-autoupgrade \

	CLUSTER_CREATE_SUCCESS="$?"
	if [ $CLUSTER_CREATE_SUCCESS != 0 ]; then
		echo >&2 "Error occured during cluster creation with gcloud."
	else 
		echo "Completed '$CLUSTER_NAME' cluster creation."
	fi
	return $CLUSTER_CREATE_SUCCESS
}

request_storage() {
	# NOTE: if storage already exists, kubernetes will handle by recognizing it already exists

	echo "Creating persistent storage volumes..."
	VCLAIMS=( "$DIRNAME/scripts/"*volumeclaim.yaml )

	for volumeclaim in $VCLAIMS; do
		$VERBOSE && echo "EXEC: kubectl apply -f ${volumeclaim}" 
		kubectl apply -f "$volumeclaim"
		STORAGE_PARTITION_SUCCESS="$?"
		if [ "$STORAGE_PARTITION_SUCCESS" != 0 ]; then
			echo >&2 "ERROR: Failed to execute/create $(basename "$volumeclaim")"
			exit $STORAGE_PARTITION_SUCCESS
		elif [ $VERBOSE ]; then
			echo "Success: kubectl apply -f ${volumeclaim}"
		fi
	done
	
	if [ ${#VCLAIMS[@]} > 0 ]; then
		echo "Waiting for storage volumes to be bound to Compute Engine..."
		# Create Loop to detect when storage volumes become bound
		ALL_BOUND=false
		COUNTER=0
		while [ $ALL_BOUND = false ]; do
			sleep 2s
			COUNTER=$((COUNTER+2))
			if [ $((COUNTER % 10)) == 0 ]; then
				VOLUME_STATUS=(\
							   $(kubectl get pvc \
							     | awk -F "[ ][ ]+" 'NR>=2 {print $2}' \
								 | awk 'toupper($0) !~ /^BOUND$/ { print }'\
								)\
							  )
				if [ ${#VOLUME_STATUS[@]} == 0 ]; then
					ALL_BOUND=true && echo;
					break
				fi
			fi
			[ $((COUNTER % 6)) == 0 ] && echo "." || echo -n "."
			[ $COUNTER -gt 180 ] && echo && echo "Storage binding time exceeded 3 minutes. Please check for errors. Exiting..." && exit 3
		done

		echo "Completed ${#VCLAIMS[@]} persistent storage volume creation."
		echo "Persistent Storage Volumes: "
		kubectl get pvc; echo;
	else
		echo "0 volume claims found." && echo;
	fi

}

increment_cluster_name() {
	if [ -n "$(echo "$1" | egrep "[0-9]+$")" ]; then
		echo "$(echo "$1" | awk '{ match($0, /[0-9]+$/); print substr($0,0,RSTART-1)int(substr($0, RSTART, RLENGTH))+1 };' )"
	else
		echo "${1}-1"
	fi
}

## Main Loop ##
main() {
	$MODE_QUIET && 1>/dev/null;
	$VERBOSE && print_banner 1>&1;
	
	# Check if cluster exists and isn't running a current instance
	CLUSTER=false
	if [ -n "$(gcloud compute instances list 2>&1 | grep $CLUSTER_NAME)" ]; then
		CLUSTER=true
		echo && echo >&2 "Current compute cluster instance running with the name $CLUSTER_NAME"
		CURRENTLY_RUNNING="$(kubectl get pods 2>&1 | grep --invert-match "No resources found.")"
		if [ -n "$CURRENTLY_RUNNING" ]; then
			# there is a current deployment running
			echo >&2 "WARN: Current deployment running on cluster '$CLUSTER_NAME'."
		fi

		CLUSTER_NAME_NEW="$(increment_cluster_name $CLUSTER_NAME)"

		RESOLUTION=true
		## STILL Broken
		while [ $RESOLUTION = false ]; do 
			echo >&2 "Do you want to create a new cluster with"
			echo >&2 -n "the name '$CLUSTER_NAME_NEW' [Y/N]: "
			
			read RESOLUTION # < "${0:-/dev/stdin}"
			if [ -z "$(echo "$RESOLUTION" | egrep --invert-match "^[ ]*([YNyn]|yes|no|YES|NO)[ ]*$" )" ]; then
				echo >&2 "InputError: Unexpected input value. Try again."
				RESOLUTION=false	# reset
			elif [ -n "$(echo "$RESOLUTION" | egrep "^[ ]*([Yy]|yes|YES)[ ]*$")" ]; then
				RESOLUTION=true
				CLUSTER_NAME="$CLUSTER_NAME_NEW"
				CLUSTER=false
			else	# No
				echo >&2 "Error: Cluster naming conflict. Please fix and try again." && exit 2
			fi
		done

		# Resolution is to use incremented name

	fi

	if [ $CLUSTER = false ]; then
		create_cluster
	fi

	# Create Persistent Storage elements for cluster
	request_storage 1>&1;
	[ "$?" != 0 ] && echo >&2 "Error occured during cluster storage creation. Exiting..." && exit 1

	echo "GKE cluster create complete." && echo;
}

# ---------------------------
# CODE START - Ingest line args
# ---------------------------
process_args "$@";

check_prereqs || exit 1;

main                    # Run Main Loop
