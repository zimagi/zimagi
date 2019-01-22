#!/bin/sh
#-------------------------------------------------------------------------------
set -e

echo '1'

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/../../app"
#-------------------------------------------------------------------------------

echo '2'

if [ -z "$DOCKER_USER" ]
then
    echo "DOCKER_USER environment variable must be defined to deploy application"
    exit 1
fi
if [ -z "$DOCKER_PASSWORD" ]
then
    echo "DOCKER_PASSWORD environment variable must be defined to deploy application"
    exit 1
fi

echo '3'

VERSION=$(cat "settings/version.py" | egrep -o '[[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+' | head -n1)

#echo "$DOCKER_PASSWORD" | docker login --username "$DOCKER_USER" --password-stdin

#docker build -f Dockerfile -t cenv/cenv:latest -t "cenv/cenv:${VERSION}" .
#docker push cenv/cenv:latest
#docker push "cenv/cenv:${VERSION}"
