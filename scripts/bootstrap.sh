#!/usr/bin/env bash
#-------------------------------------------------------------------------------

set -e

export DEBIAN_FRONTEND=noninteractive

PROJ_DIR="${1}" # Required!!
cd "$PROJ_DIR"

#-------------------------------------------------------------------------------

#install basic dependencies
echo "> Updating OS package repositories"
sudo apt-get update >/dev/null 2>&1

#install basic dependencies
if ! which git >/dev/null
then
  echo "> Installing Git version control"
  sudo apt-get install -y git >/dev/null 2>&1
fi

echo "> Installing package management utilities"
sudo apt-get install -y software-properties-common >/dev/null 2>&1

#install Python
./scripts/setup-python.sh

#install Kubernetes CLI
./scripts/setup-kubernetes.sh

#Copy executable shortcuts
./scripts/link-commands.sh
