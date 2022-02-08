#!/bin/bash
#-------------------------------------------------------------------------------
set -e

export __zimagi_docker_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export __zimagi_base="$(basename ${BASH_SOURCE[0]})"
export __zimagi_dir="$(dirname "${__zimagi_docker_dir}")"
export __zimagi_script_dir="${__zimagi_dir}/scripts"

source "${__zimagi_script_dir}/variables.sh"

RUNTIME="${1:-standard}"
VERSION="${2}"
PKG_DOCKER_IMAGE="${PKG_DOCKER_IMAGE:-$DEFAULT_BASE_IMAGE}"
#-------------------------------------------------------------------------------

if [ -z "$VERSION" ]; then
    VERSION="$(cat app/VERSION)"
fi

if [ -z "$PKG_DOCKER_USER" ]; then
    echo "PKG_DOCKER_USER environment variable must be defined to deploy application"
    exit 1
fi
if [ -z "$PKG_DOCKER_PASSWORD" ]; then
    echo "PKG_DOCKER_PASSWORD environment variable must be defined to deploy application"
    exit 1
fi

echo "Logging into DockerHub"
echo "$PKG_DOCKER_PASSWORD" | docker login --username "$PKG_DOCKER_USER" --password-stdin

if [ "$RUNTIME" = "standard" ]; then
    ZIMAGI_TAG="$VERSION"
    ZIMAGI_PARENT_IMAGE="$DOCKER_STANDARD_PARENT_IMAGE"
else
    ZIMAGI_TAG="${RUNTIME}-${VERSION}"

    if [ "$RUNTIME" == "nvidia" ]; then
        ZIMAGI_PARENT_IMAGE="$DOCKER_NVIDIA_PARENT_IMAGE"
    else
        echo "Zimagi Docker runtime not supported: ${RUNTIME}"
        exit 1
    fi
fi

echo "Ensuring modules directory"
mkdir -p "${__zimagi_lib_dir}/modules"

echo "Building Docker image: ${ZIMAGI_TAG}"
docker build --force-rm --no-cache \
    --file "${__zimagi_docker_dir}/Dockerfile" \
    --tag "${PKG_DOCKER_IMAGE}:${ZIMAGI_TAG}" \
    --build-arg ZIMAGI_PARENT_IMAGE \
    --build-arg ZIMAGI_USER_UID \
    --build-arg ZIMAGI_USER_PASSWORD \
    --build-arg ZIMAGI_CA_KEY \
    --build-arg ZIMAGI_CA_CERT \
    --build-arg ZIMAGI_KEY \
    --build-arg ZIMAGI_CERT \
    --build-arg ZIMAGI_DATA_KEY \
    "${__zimagi_dir}"

echo "Pushing Docker image: ${ZIMAGI_TAG}"
docker push "${PKG_DOCKER_IMAGE}:${ZIMAGI_TAG}"
