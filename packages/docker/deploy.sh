#!/bin/sh
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/../.."
#-------------------------------------------------------------------------------

if [ -z "$PKG_DOCKER_USER" ]
then
    echo "PKG_DOCKER_USER environment variable must be defined to deploy application"
    exit 1
fi
if [ -z "$PKG_DOCKER_PASSWORD" ]
then
    echo "PKG_DOCKER_PASSWORD environment variable must be defined to deploy application"
    exit 1
fi

VERSION=$(cat "app/settings/version.py" | egrep -o '[[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+' | head -n1)

echo "Logging into DockerHub"
echo "$PKG_DOCKER_PASSWORD" | docker login --username "$PKG_DOCKER_USER" --password-stdin

echo "Building Docker image"
docker build -f app/Dockerfile -t cenv/cenv:latest -t "cenv/cenv:${VERSION}" .

echo "Pushing Docker image with tags"
docker push cenv/cenv:latest
docker push "cenv/cenv:${VERSION}"
