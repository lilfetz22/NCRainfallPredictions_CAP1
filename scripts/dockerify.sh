#!/bin/bash
#
# FILE: dockerify.sh
#=========================================
# Instructions to build Docker container
#
# Usage:
#	$> ./dockerify.sh [options]
# 
# For Options, see help
#   $> ./dockerify.sh --help
#=========================================

DIRNAME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd )" && DIRNAME="${DIRNAME%/scripts}";
BUILD_DIR="build"
IMAGE_DIR="bin"
AUTHOR="lilFetz22"
REPO="$AUTHOR"
NAME="rainfall"

usage() {
	echo "Usage: ./$(basename "$0") [-q | --quiet] [--no-rebuild] [-v <#> | --version=<#>]" 1>&2;
	echo "       ./$(basename "$0") [-h | --help]" 1>&2;
	exit 1;
}
help() {
    echo ""
    echo " Rainfall Estimation Docker Creation Script "
    echo "--------------------------------------------"
    echo "Docker build script.  Docker packages app files, tags with version and" \
		 "saves Docker container image." \
    	 "Docker image files are saved to the ${DIRNAME%/}/$IMAGE_DIR directory.";
    usage | echo;
	echo "";
    echo "Available Options: "
    echo "  -h | --help   Help"
	echo "  -q | --quiet  Execute quietly except for errors"
	echo "  -v <#> | --version=<#>  Tags docker image with specified version number"
	echo "  --no-rebuild  Makes container with current ./build files, fails if empty"
    echo "";
	echo "DEFAULT VARS:";
	echo "  AUTHOR: $AUTHOR";
	echo "  IMAGE_NAME: $REPO/$NAME:latest"
	echo "  BUILD_DIR: $(basename "$DIRNAME")/$BUILD_DIR";
	echo "";
    # echo "ENVIRONMENT VARS:"
    # echo "  DIRNAME, BUILD_DIR, VERBOSE"
    # echo ""
    exit 0;
}
print_banner() {
	echo "";
    echo "=====================================";
    echo "|   Rainfall Estimation Dockerify   |";
    echo "=====================================";
	echo "START: $(date)";
	echo "";
}

check_prereqs() {
	missing_prereqs=0
	command -v docker >/dev/null 2>&1 || { ((missing_prereqs++)); echo >&2 "MISSING PREREQ: docker is not installed but is required."; }
	# List additional prereqs here
	return "$missing_prereqs"
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
			-v|--version)
				if [ "$2" ]; then
					VERSION="${2}"
					shift
				else
					usage;
				fi
				;;
			"--version"=?*)
				OPTARG=${1#*=} 			# Delete everything up to "=" and keep the remainder.
				TARGET_PAGE="${OPTARG}"
				;;
			"--version"=)						# Handle the case of an empty --path=
				usage;
				;;
			--no-rebuild)
				REBUILD=false
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
	[ -z "$REBUILD" ] && REBUILD=true
	[ -z "$VERSION" ] && VERSION=""
	[ -z "$MODE_QUIET" ] && MODE_QUIET=false

}

main() {
	[ $MODE_QUIET = true ] && exec 1>/dev/null;
	print_banner 1>&1;

	if [ $REBUILD = true ]; then
		# ensure build files are up to date
		echo "[DOCKERIFY] Running build script...";
		BUILD_DIR="$BUILD_DIR" "$DIRNAME/scripts/build.sh" &
		pid=$!
		wait $pid || { echo "[DOCKERIFY] build failed. Aborting..." 2>&2 && echo && exit 1; }
		echo "[DOCKERIFY] Build completed!"

	elif [ -z "$(ls -al "$DIRNAME/$BUILD_DIR" | egrep --invert-match '^(.*[ ]((\.)|(\.\.))$)|(total.*$)')" ]; then
		# build folder is empty
		echo "MISSING FILES: build directory is empty." >&2 && echo && exit 1;
	fi

	if [ ! -d "$DIRNAME/$IMAGE_DIR" ]; then
		echo "[DOCKERIFY] Creating Directory: "
		echo -n "[DOCKERIFY]   " && echo "$DIRNAME/$IMAGE_DIR"	# macosx mkdir -p -v [path] fails, is official bug
		mkdir -p "$DIRNAME/$IMAGE_DIR"
	fi

	[ -z $VERSION ] && TAG="" || TAG="--tag '$REPO/$NAME:$VERSION'";

	IMAGE_NAME="${NAME}_$([ -z $VERSION ] && echo "latest" || echo "$VERSION")"

	echo "[DOCKERIFY] Creating Docker Container...";
	# docker build [tag(s), output destination, PATH/directory of Dockerfile & context]
	echo "[DOCKERIFY]" \
			"docker build" \
				$TAG \
				--tag "$REPO/$NAME:latest" \
				--output "$DIRNAME/$IMAGE_DIR/$IMAGE_NAME.tar" \
				"$DIRNAME"
	
	# actual command
	docker build \
		$TAG \
		--tag "$REPO/$NAME:latest" \
		--output "$DIRNAME/$IMAGE_DIR/$IMAGE_NAME.tar" \
		"$DIRNAME"
	
	# Handle Docker build status 
	if [ "$?" != 0 ]; then
		echo "[DOCKERIFY] Error occured.  Aborting..." >&2 && echo && exit 1;
	else
		echo && echo "[DOCKERIFY] SUCCESS: Docker image created at $IMAGE_DIR/$IMAGE_NAME.tar" && echo;
		# Instructions
		echo "  NEXT STEPS  "
		echo " ------------ "
		echo "1. Connect to docker server instance.";
		echo "2. Load this docker image with the command: "
		echo "     $ docker load -i <path/to/$IMAGE_NAME.tar>"
		echo "";
		# echo "OR";
		# echo "1. Run Deploy script";
		# echo "     $ ./scripts/deploy.sh <target_environment>"
		# echo "";
	fi
}

# ------------------------------
# CODE START - Ingest line args
# ------------------------------
process_args "$@";

check_prereqs || exit 1;

main                    # Run Main Loop
exit 0;
