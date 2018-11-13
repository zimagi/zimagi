#!/usr/bin/env bash
# Update host user password on all ansible nodes

set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

ENVIRONMENT="${1:-dev}"
PLAYBOOK_CONFIG="playbooks/password.yml"
ENV_CONFIG="playbooks/password.${ENVIRONMENT}.yml"

# Get sudo password
echo -n "Current password: " 
read -s PASSWORD

echo -n "New password: " 
read -s NEW_PASSWORD

echo -n "Retype new password: " 
read -s CONFIRM_PASSWORD
echo

if [ "$NEW_PASSWORD" != "$CONFIRM_PASSWORD" ]
then
  echo "New password does not match!"
  exit 1   
fi

#-------------------------------------------------------------------------------

# Generate fresh host configuration
./scripts/gen-host-config.py "$ENVIRONMENT"

# Ensure the SSH keys are situated properly
./scripts/update-keys.py "$ENVIRONMENT"

# Provision cluster nodes
if [ -f "$ENV_CONFIG" ]
then
  PLAYBOOK_CONFIG="$ENV_CONFIG"
fi
ansible-playbook --become "$PLAYBOOK_CONFIG" --extra-vars "ansible_become_pass=$PASSWORD updated_password=$NEW_PASSWORD cluster_environment=$ENVIRONMENT"
