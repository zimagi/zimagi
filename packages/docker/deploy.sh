#!/bin/sh
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/../../app"
#-------------------------------------------------------------------------------

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

VERSION=$(cat "settings/version.py" | egrep -o '[[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+' | head -n1)

echo "Logging into DockerHub"
echo "$DOCKER_PASSWORD" | docker login --username "$DOCKER_USER" --password-stdin

echo "Building Dockerfile"
docker build -f Dockerfile -t cenv/cenv:latest -t "cenv/cenv:${VERSION}" .

echo "Pushing Docker image tags"
docker push cenv/cenv:latest
docker push "cenv/cenv:${VERSION}"
