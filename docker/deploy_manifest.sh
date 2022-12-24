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

echo "Creating Docker manifest: ${ZIMAGI_TAG}"
ZIMAGI_TAG="$VERSION"

if [ "$RUNTIME" = "standard" ]; then
    docker manifest create "${PKG_DOCKER_IMAGE}:${ZIMAGI_TAG}" \
        --amend "${PKG_DOCKER_IMAGE}:${ZIMAGI_TAG}-amd64" \
        --amend "${PKG_DOCKER_IMAGE}:${ZIMAGI_TAG}-arm64" 
else
    ZIMAGI_TAG="${RUNTIME}-${ZIMAGI_TAG}"

    if [ "$RUNTIME" != "nvidia" ]; then
        echo "Zimagi Docker runtime not supported: ${RUNTIME}"
        exit 1
    fi

    docker manifest create "${PKG_DOCKER_IMAGE}:${ZIMAGI_TAG}" \
        --amend "${PKG_DOCKER_IMAGE}:${ZIMAGI_TAG}-amd64"
fi

echo "Pushing Docker manifest: ${ZIMAGI_TAG}"
docker manifest push "${PKG_DOCKER_IMAGE}:${ZIMAGI_TAG}"
