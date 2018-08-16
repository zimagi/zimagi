#!/usr/bin/env bash
# Setup Ansible.

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

LOG_FILE="${1:-./logs/ansible.log}"
if [ "$LOG_FILE" != "/dev/stdout" -a "$LOG_FILE" != "/dev/stderr" ]
then
  rm -f "$LOG_FILE"
fi

#install Ansible if it does not exist
echo "> Adding Ansible package repository" | tee -a "$LOG_FILE"
apt-add-repository -y ppa:ansible/ansible >"$LOG_FILE" 2>&1
apt-get update >"$LOG_FILE" 2>&1
  
echo "> Installing Ansible" | tee -a "$LOG_FILE"
apt-get install -y ansible >"$LOG_FILE" 2>&1