#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."
#-------------------------------------------------------------------------------

VERSION=$(cat "settings/version.py" | egrep -o '[[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+' | head -n1)

docker login

docker build -f Dockerfile -t cenv/cenv:latest -t "cenv/cenv:${VERSION}" .
docker push cenv/cenv:latest
docker push "cenv/cenv:${VERSION}"
