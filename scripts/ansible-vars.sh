#!/usr/bin/env bash
# Create an initial Kubenetes cluster with inventory and configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

ENVIRONMENT="${1:-dev}"
TYPE="${2:-cluster}"
PLAYBOOK_CONFIG="playbooks/vars.yml"

#-------------------------------------------------------------------------------

# Generate fresh host configuration
./scripts/gen-host-config.py "$ENVIRONMENT"

# Ensure the SSH keys are situated properly
./scripts/update-keys.py "$ENVIRONMENT"

ansible-playbook "$PLAYBOOK_CONFIG" --extra-vars "cluster_environment=$ENVIRONMENT"
