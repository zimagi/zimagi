#!/bin/bash
#-------------------------------------------------------------------------------
set -e

export __zimagi_docker_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export __zimagi_dir="$(dirname "${__zimagi_docker_dir}")"

source "${__zimagi_dir}/.env"
#-------------------------------------------------------------------------------

ZIMAGI_BUILD_IMAGE="zimagi/client:$(cat "${__zimagi_dir}/app/VERSION")"

echo "Building Zimagi Client Docker image: ${ZIMAGI_BUILD_IMAGE}"
docker build --force-rm --no-cache \
    --file "${__zimagi_docker_dir}/Dockerfile.client" \
    --tag "$ZIMAGI_BUILD_IMAGE" \
    --build-arg ZIMAGI_USER_UID \
    --build-arg ZIMAGI_USER_PASSWORD \
    --build-arg ZIMAGI_ENVIRONMENT=local \
    "${__zimagi_dir}"
