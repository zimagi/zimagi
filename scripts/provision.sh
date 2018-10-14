#!/usr/bin/env bash
# Create an initial Kubenetes cluster with inventory and configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

ENVIRONMENT="${1:-dev}"

# Get sudo password
echo -n "Password: " 
read -s PASSWORD
echo

#-------------------------------------------------------------------------------

# Ensure the SSH keys are situated properly
./scripts/update-keys.py

# Generate fresh host configuration
./scripts/gen-host-config.py "$ENVIRONMENT"

# Provision cluster nodes
ansible-playbook --become update-cluster.yml --extra-vars "ansible_become_pass=$PASSWORD"
