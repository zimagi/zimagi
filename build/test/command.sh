#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
HOME_DIR="$SCRIPT_DIR/../.."
#-------------------------------------------------------------------------------
echo "Preparing  Zimagi"
"$HOME_DIR"/zimagi env get
"$HOME_DIR"/zimagi user list

echo "Running Zimagi command tests"
"$HOME_DIR"/zimagi test --types=command
