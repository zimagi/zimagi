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
    cat <<EOF >&2

Run a suite of Zimagi tests

Usage:

  test/exec.sh [flags] [options]

Flags:

    -h --help                         Display help information
    -q --quiet                        Run setup process but do not render terminal output
    -e --skip-binary                  Skip downloading binary executables
    -b --skip-build                   Skip Docker image build step

Options:

    --script <command>                Test script name (command or api)
    --name <zimagi>                   Application name for this Zimagi platform buildout
    --runtime <standard>              Zimagi Docker runtime (standard or nvidia)
    --tag <dev>                       Zimagi Docker tag
    --data-key <0123456789876543210>  Zimagi data encryption key built into Docker image

EOF
    exit 1
}

while [[ $# -gt 0 ]]
do
    case "$1" in
        --name=*)
        APP_NAME="${1#*=}"
        ;;
        --name)
        APP_NAME="$2"
        shift
        ;;
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
        -q|--quiet)
        QUIET=1
        ;;
        -h|--help)
        usage
        ;;
        *)
        ARGS+=("$1")
        ;;
    esac
    shift
done

APP_NAME=${APP_NAME:-zimagi}
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
export ZIMAGI_DISPLAY_COLOR="${ZIMAGI_DISPLAY_COLOR:-False}"
export ZIMAGI_DISABLE_PAGE_CACHE="${ZIMAGI_DISABLE_PAGE_CACHE:-True}"
export ZIMAGI_TEST_KEY="${ZIMAGI_TEST_KEY:-RFJwNYpqA4zihE8jVkivppZfGVDPnzcq}"
export ZIMAGI_STARTUP_SERVICES=${ZIMAGI_STARTUP_SERVICES:-'["scheduler", "worker", "command-api", "data-api"]'}
export ZIMAGI_COMMAND_HOST_PORT="${ZIMAGI_COMMAND_HOST_PORT:-5123}"
export ZIMAGI_DATA_HOST_PORT="${ZIMAGI_DATA_HOST_PORT:-5323}"
#-------------------------------------------------------------------------------

print "Preparing Zimagi ${DOCKER_RUNTIME}"
./reactor init "$APP_NAME" --runtime="$DOCKER_RUNTIME" "${ARGS[@]}" 1>$OUTPUT_DEVICE 2>$ERROR_DEVICE
./zimagi env get 1>$OUTPUT_DEVICE 2>$ERROR_DEVICE

print "Starting Zimagi ${DOCKER_RUNTIME} test script execution"
./test/"${TEST_SCRIPT}.sh" "$DOCKER_RUNTIME" 1>$OUTPUT_DEVICE 2>$ERROR_DEVICE
