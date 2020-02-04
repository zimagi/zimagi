#!/bin/sh
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/../.."

PKG_DOCKER_IMAGE="${PKG_DOCKER_IMAGE:-mcmi/mcmi}"
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

echo "Logging into DockerHub"
echo "$PKG_DOCKER_PASSWORD" | docker login --username "$PKG_DOCKER_USER" --password-stdin

echo "Building latest Docker image"
docker build \
    --build-arg MCMI_CA_KEY \
    --build-arg MCMI_CA_CERT \
    --build-arg MCMI_KEY \
    --build-arg MCMI_CERT \
    --file app/Dockerfile \
    --tag "${PKG_DOCKER_IMAGE}:latest" .

echo "Pushing latest Docker image"
docker push "${PKG_DOCKER_IMAGE}:latest"
