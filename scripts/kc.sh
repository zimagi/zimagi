#!/usr/bin/env bash
# Manage a running Kubernetes cluster given a generated environment configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

ENVIRONMENT="${1}"
ARGS="${@:2}"
KUBE_CONFIG="config/admin.${ENVIRONMENT}.conf"

if [ -z "$ENVIRONMENT" ]
then
  echo "ERROR: Environment required as first parameter"
  exit 1
fi

#-------------------------------------------------------------------------------

kubectl --kubeconfig="$KUBE_CONFIG" $ARGS
