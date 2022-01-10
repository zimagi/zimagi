#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
HOME_DIR="$SCRIPT_DIR/../.."

export ZIMAGI_DISPLAY_COLOR=False
export ZIMAGI_DEBUG=True
export ZIMAGI_DISABLE_PAGE_CACHE=True
export ZIMAGI_TEST_KEY="${ZIMAGI_TEST_KEY:-RFJwNYpqA4zihE8jVkivppZfGVDPnzcq}"
#-------------------------------------------------------------------------------
echo "Preparing Zimagi environment"
"$HOME_DIR"/scripts/setup.sh

echo "Starting Zimagi services"
docker-compose up -d command-api
sleep 10
docker-compose up -d data-api scheduler worker
sleep 60

STOPPED_SERVICES=""

declare -a services=("command-api" "data-api" "scheduler" "worker")
for service in "${services[@]}"
do
    if ! docker-compose ps --services --filter "status=running" | grep "$service"
    then
        STOPPED_SERVICES="TRUE"
    fi
done
if [ ! -z "$STOPPED_SERVICES" ]
then
    echo "Application services no longer running"
    docker-compose ps
    docker-compose logs
    exit 1
fi

echo "Setting Zimagi host"
"$HOME_DIR"/zimagi host save default host=localhost encryption_key="$ZIMAGI_TEST_KEY"
"$HOME_DIR"/zimagi env get
"$HOME_DIR"/zimagi user list

echo "Running Zimagi API tests"
"$HOME_DIR"/zimagi test --types=api
