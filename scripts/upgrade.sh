#!/usr/bin/env bash
# Safely upgrade an existing Kubenetes cluster with inventory and configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

#-------------------------------------------------------------------------------

# Ensure the SSH keys are situated properly
./scripts/update-keys.py

# Generate fresh host configuration
./scripts/gen-host-config.py

# Provision Kubernetes cluster
ansible-playbook kubespray/upgrade-cluster.yml
