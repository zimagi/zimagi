#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
HOME_DIR="$SCRIPT_DIR/../.."

export ZIMAGI_DISPLAY_COLOR=False
export ZIMAGI_DEBUG=True
export ZIMAGI_DISABLE_PAGE_CACHE=True
#-------------------------------------------------------------------------------
echo "Preparing Zimagi"
"$HOME_DIR"/scripts/build.sh

"$HOME_DIR"/zimagi env get
"$HOME_DIR"/zimagi user list

echo "Running Zimagi command tests"
"$HOME_DIR"/zimagi test --types=command
