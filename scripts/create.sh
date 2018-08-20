#!/usr/bin/env bash
# Create an initial Kubenetes cluster with inventory and configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

PASSWORD="${1}" # Required!!

#-------------------------------------------------------------------------------

# Ensure the SSH keys are situated properly
./scripts/update-keys.py

# Generate fresh host configuration
./scripts/gen-host-config.py

# Initialize cluster nodes
ansible-playbook init-cluster.yml --extra-vars "ansible_become_pass=$PASSWORD"

# Provision Kubernetes cluster
ansible-playbook kubespray/cluster.yml --extra-vars "ansible_become_pass=$PASSWORD"
