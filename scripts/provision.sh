#!/usr/bin/env bash
# Create an initial Kubenetes cluster with inventory and configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

ENVIRONMENT="${1:-dev}"
CLUSTER_CONFIG="playbooks/cluster.yml"
ENV_CONFIG="playbooks/cluster.${ENVIRONMENT}.yml"

# Get sudo password
echo -n "Password: " 
read -s PASSWORD
echo

#-------------------------------------------------------------------------------

# Generate fresh host configuration
./scripts/gen-host-config.py "$ENVIRONMENT"

# Ensure the SSH keys are situated properly
./scripts/update-keys.py "$ENVIRONMENT"

# Provision cluster nodes
if [ -f "$ENV_CONFIG" ]
then
  CLUSTER_CONFIG="$ENV_CONFIG"
fi

ansible-playbook --become "$CLUSTER_CONFIG" --extra-vars "ansible_become_pass=$PASSWORD"
