#!/usr/bin/env bash
# Create an initial Kubenetes cluster with inventory and configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

ENVIRONMENT="${1:-dev}"
TYPE="${2:-cluster}"
PLAYBOOK_CONFIG="playbooks/${TYPE}.yml"
ENV_CONFIG="playbooks/${TYPE}.${ENVIRONMENT}.yml"

# Get sudo password
echo -n "Password: " 
read -s PASSWORD
echo

#-------------------------------------------------------------------------------

# Ensure Kubernetes configuration directory
mkdir -p "${HOME}/.kube"

# Generate fresh host configuration
./scripts/gen-host-config.py "$ENVIRONMENT"

# Ensure the SSH keys are situated properly
./scripts/update-keys.py "$ENVIRONMENT"

# Provision cluster nodes
if [ -f "$ENV_CONFIG" ]
then
  PLAYBOOK_CONFIG="$ENV_CONFIG"
fi
ansible-playbook --become "$PLAYBOOK_CONFIG" --extra-vars "ansible_become_pass=$PASSWORD cluster_environment=$ENVIRONMENT"

# Setup kubectl configuration file
rm -f "config/admin.${ENVIRONMENT}.conf"
mv "config/admin.conf" "config/admin.${ENVIRONMENT}.conf"
cp -f "config/admin.${ENVIRONMENT}.conf" "${HOME}/.kube/config"

# Manage Kubernetes resources
for filename in components/*.yml
do
  kubectl apply -f "$filename"  
done
