#!/bin/sh
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/../.."

PKG_DOCKER_IMAGE="${PKG_DOCKER_IMAGE:-zimagi/zimagi}"
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

echo "Building versioned Docker image"
docker build \
    --build-arg ZIMAGI_CA_KEY \
    --build-arg ZIMAGI_CA_CERT \
    --build-arg ZIMAGI_KEY \
    --build-arg ZIMAGI_CERT \
    --file app/Dockerfile \
    --tag "${PKG_DOCKER_IMAGE}:${VERSION}" .

echo "Pushing versioned Docker image"
docker push "${PKG_DOCKER_IMAGE}:${VERSION}"
