#!/bin/bash
#-------------------------------------------------------------------------------
set -e

export __zimagi_docker_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export __zimagi_dir="$(dirname "${__zimagi_docker_dir}")"

export ZIMAGI_ENVIRONMENT="${1:-local}"
#-------------------------------------------------------------------------------

ZIMAGI_VERSION=$(cat "${__zimagi_dir}/app/VERSION")
ZIMAGI_BUILD_IMAGE="zimagi/cli:${ZIMAGI_VERSION}"

echo "Building Zimagi Client Docker image: ${ZIMAGI_BUILD_IMAGE}"
docker build \
    --file "${__zimagi_docker_dir}/Dockerfile.cli" \
    --tag "$ZIMAGI_BUILD_IMAGE" \
    --build-arg ZIMAGI_ENVIRONMENT="$ZIMAGI_ENVIRONMENT" \
    "${__zimagi_dir}"
