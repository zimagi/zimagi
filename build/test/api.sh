#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
HOME_DIR="$SCRIPT_DIR/../.."

ZIMAGI_TEST_KEY="${ZIMAGI_TEST_KEY:-RFJwNYpqA4zihE8jVkivppZfGVDPnzcq}"
#-------------------------------------------------------------------------------
echo "Preparing  Zimagi environment"
"$HOME_DIR"/scripts/build.sh

echo "Starting Zimagi services"
docker-compose up -d command-api
sleep 10
docker-compose up -d data-api scheduler worker

echo "Setting Zimagi host"
"$HOME_DIR"/zimagi host save default host=localhost encryption_key="$ZIMAGI_TEST_KEY"
"$HOME_DIR"/zimagi env get
"$HOME_DIR"/zimagi user list

echo "Running Zimagi API tests"
"$HOME_DIR"/zimagi test --types=api
