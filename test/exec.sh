#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
HOME_DIR="$SCRIPT_DIR/.."
cd "$HOME_DIR"

QUIET=0
ARGS=()


print() {
    if [ $QUIET -ne 1 ]
    then
        echo "$@"
    fi
}

print_error() {
    if [ $QUIET -ne 1 ]
    then
        echo "$@" 1>&2
    fi
}


usage() {
    cat << USAGE >&2
Usage:
    test/exec.sh
    -h | --help         Display help information
    --script=SCRIPT     Test script name (defaults to: command)
    --name=NAME         Application name for this Zimagi platform buildout (defaults to: zimagi)
    --tag=TAG           Built Docker image tag or tag suffix if runtime supplied (defaults to: dev)
    --runtime=RUNTIME   Runtime name for Docker image (defaults to: standard)
    --skip-build        Run setup process but skip Docker build process (useful if image already exists)
    --quiet             Run setup process but do not render terminal output
USAGE
    exit 0
}


while [[ $# -gt 0 ]]
do
    case "$1" in
        --script=*)
        TEST_SCRIPT="${1#*=}"
        ;;
        --script)
        TEST_SCRIPT="$2"
        shift
        ;;
        --runtime=*)
        DOCKER_RUNTIME="${1#*=}"
        ;;
        --runtime)
        DOCKER_RUNTIME="$2"
        shift
        ;;
        --quiet)
        QUIET=1
        ;;
        -h | --help)
        usage
        ;;
        *)
        ARGS+=("$1")
        ;;
    esac
    shift
done

DOCKER_RUNTIME=${DOCKER_RUNTIME:-standard}
TEST_SCRIPT=${TEST_SCRIPT:-command}

if [ $QUIET -ne 1 ]
then
    OUTPUT_DEVICE=/dev/stdout
    ERROR_DEVICE=/dev/stderr
else
    OUTPUT_DEVICE=/dev/null
    ERROR_DEVICE=/dev/null
fi
#-------------------------------------------------------------------------------
export ZIMAGI_DISPLAY_COLOR=False
export ZIMAGI_DISABLE_PAGE_CACHE=True
export ZIMAGI_TEST_KEY="${ZIMAGI_TEST_KEY:-RFJwNYpqA4zihE8jVkivppZfGVDPnzcq}"
export ZIMAGI_STARTUP_SERVICES='["scheduler", "worker", "command-api", "data-api"]'
export ZIMAGI_COMMAND_HOST_PORT=5123
export ZIMAGI_DATA_HOST_PORT=5323
#-------------------------------------------------------------------------------

print "Preparing Zimagi ${DOCKER_RUNTIME}"
./setup --runtime="$DOCKER_RUNTIME" "${ARGS[@]}" 1>$OUTPUT_DEVICE 2>$ERROR_DEVICE
./zimagi env get 1>$OUTPUT_DEVICE 2>$ERROR_DEVICE

print "Starting Zimagi ${DOCKER_RUNTIME} test script execution"
./test/"${TEST_SCRIPT}.sh" "$DOCKER_RUNTIME" 1>$OUTPUT_DEVICE 2>$ERROR_DEVICE
