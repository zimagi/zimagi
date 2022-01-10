#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
HOME_DIR="$SCRIPT_DIR/.."

TEST_SCRIPT="${1}"

export ZIMAGI_DISPLAY_COLOR=False
export ZIMAGI_DEBUG=True
export ZIMAGI_DISABLE_PAGE_CACHE=True
export ZIMAGI_TEST_KEY="${ZIMAGI_TEST_KEY:-RFJwNYpqA4zihE8jVkivppZfGVDPnzcq}"
export ZIMAGI_STARTUP_SERVICES='["postgresql", "redis", "scheduler", "worker", "command-api", "data-api"]'
export ZIMAGI_COMMAND_HOST_PORT=5123
export ZIMAGI_DATA_HOST_PORT=5323
#-------------------------------------------------------------------------------
cd "$HOME_DIR"

if [ -z "$TEST_SCRIPT" ]
then
    echo "TEST_SCRIPT argument required for test wrapper"
    exit 1
fi

for DOCKER_FILE in "$SCRIPT_DIR"/Dockerfile*
do
    RUNTIME="${DOCKER_FILE#*.}"

    if [ "$RUNTIME" == "$DOCKER_FILE" ]
    then
        RUNTIME="standard"
    fi

    echo "Preparing Zimagi ${RUNTIME}"
    sudo ./setup "$RUNTIME"
    ./zimagi env get

    ./test/"${TEST_SCRIPT}.sh" "$RUNTIME"

    echo "Cleaning up"
    ./scripts/clean-docker.sh
    rm -Rf data
    rm -Rf lib
done
