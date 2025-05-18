#!/bin/bash
#-------------------------------------------------------------------------------
set -e

export __script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${__script_dir}/shared.sh"
#-------------------------------------------------------------------------------

export ZIMAGI_DOCKER_RUNTIME="nvidia"

server_build_args
