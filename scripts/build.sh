#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

LOG_FILE="${1:-/dev/stderr}"
SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

#-------------------------------------------------------------------------------

VERSION=$(cat "app/settings/version.py" | egrep -o '[[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+' | head -n1)

docker login

docker build -f app/Dockerfile -t cenv/cenv:latest -t "cenv/cenv:${VERSION}" . >>"$LOG_FILE" 2>&1
docker push cenv/cenv:latest >>"$LOG_FILE" 2>&1
docker push "cenv/cenv:${VERSION}" >>"$LOG_FILE" 2>&1
