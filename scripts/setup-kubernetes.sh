#!/usr/bin/env bash
# Setup Kubernetes environment.

set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

LOG_FILE="${1:-./logs/kubernetes.log}"
if [ "$LOG_FILE" != "/dev/stdout" -a "$LOG_FILE" != "/dev/stderr" ]
then
  rm -f "$LOG_FILE"
fi

echo "> Adding Kubernetes package repository" | tee -a "$LOG_FILE"
curl -o /tmp/kubernetes.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg >>"$LOG_FILE" 2>&1
apt-key add /tmp/kubernetes.gpg >>"$LOG_FILE" 2>&1

touch /etc/apt/sources.list.d/kubernetes.list >>"$LOG_FILE" 2>&1 
echo "deb http://apt.kubernetes.io/ kubernetes-xenial main" > /etc/apt/sources.list.d/kubernetes.list
apt-get update >>"$LOG_FILE" 2>&1

echo "> Installing Kubernetes CLI utilities" | tee -a "$LOG_FILE"
apt-get install -y kubectl >>"$LOG_FILE" 2>&1
