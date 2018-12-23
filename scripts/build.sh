#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

LOG_FILE="${1:-/dev/stderr}"
SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

#-------------------------------------------------------------------------------

docker build -f app/Dockerfile -t cenv . >>"$LOG_FILE" 2>&1
