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
	"$SCRIPT_FILE" "$@"
}

# ---------------------------
# CODE START - Ingest line args
# ---------------------------
process_args "$@";

deploy
exit 0;
