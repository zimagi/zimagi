#!/usr/bin/env bash
# Configure local Kubernetes CLI utilities from a managed Kubernetes cluster

set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

ENVIRONMENT="${1:-dev}"
PLAYBOOK_CONFIG="playbooks/client.yml"

# Get sudo password
echo -n "Password: " 
read -s PASSWORD
echo

#-------------------------------------------------------------------------------

# Generate fresh host configuration
./scripts/gen-host-config.py "$ENVIRONMENT"

# Ensure the SSH keys are situated properly
./scripts/update-keys.py "$ENVIRONMENT"

# Retrieve Kubernetes configuration information
ansible-playbook --become "$PLAYBOOK_CONFIG" --extra-vars "ansible_become_pass=$PASSWORD cluster_environment=$ENVIRONMENT"

# Ensure Helm Tiller server is at latest version
helm init --upgrade