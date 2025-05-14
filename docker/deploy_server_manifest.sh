#!/bin/bash
#-------------------------------------------------------------------------------
set -e

export __zimagi_docker_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export __zimagi_dir="$(dirname "${__zimagi_docker_dir}")"
cd "${__zimagi_dir}"

if [ -z "$PKG_DOCKER_USER" ]; then
    echo "PKG_DOCKER_USER environment variable must be defined to deploy application"
    exit 1
fi
if [ -z "$PKG_DOCKER_PASSWORD" ]; then
    echo "PKG_DOCKER_PASSWORD environment variable must be defined to deploy application"
    exit 1
fi

export ZIMAGI_DOCKER_IMAGE="zimagi/server"
export ZIMAGI_DOCKER_RUNTIME="${1:-standard}"

export ZIMAGI_DOCKER_TAG="${2:-}"
if [ -z "$ZIMAGI_DOCKER_TAG" ]; then
    export ZIMAGI_DOCKER_TAG="$(cat "${__zimagi_dir}/app/VERSION")"
fi

if [ ! -d /tmp/reactor ]; then
    git clone --depth 1 https://github.com/kube-reactor/core.git /tmp/reactor
fi
source /tmp/reactor/bin/core/env.sh
zimagi_environment

#-------------------------------------------------------------------------------

echo "Logging into DockerHub"
echo "$PKG_DOCKER_PASSWORD" | docker login --username "$PKG_DOCKER_USER" --password-stdin

echo "Creating Docker manifest: ${ZIMAGI_DOCKER_TAG}"
if [ "$ZIMAGI_DOCKER_RUNTIME" = "standard" ]; then
    docker manifest create "${ZIMAGI_DOCKER_IMAGE}:${ZIMAGI_DOCKER_TAG}" \
        --amend "${ZIMAGI_DOCKER_IMAGE}:${ZIMAGI_DOCKER_TAG}-amd64" \
        --amend "${ZIMAGI_DOCKER_IMAGE}:${ZIMAGI_DOCKER_TAG}-arm64"
else
    docker manifest create "${ZIMAGI_DOCKER_IMAGE}:${ZIMAGI_DOCKER_TAG}" \
        --amend "${ZIMAGI_DOCKER_IMAGE}:${ZIMAGI_DOCKER_TAG}-amd64"
fi

echo "Pushing Docker manifest: ${ZIMAGI_DOCKER_TAG}"
docker manifest push "${ZIMAGI_DOCKER_IMAGE}:${ZIMAGI_DOCKER_TAG}"
