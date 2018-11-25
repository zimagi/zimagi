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

echo "> Ensuring package management utilities"
sudo apt-get install -y software-properties-common >/dev/null 2>&1

echo "> Installing network tools"
sudo apt-get install -y net-tools >/dev/null 2>&1

echo "> Ensuring Git version control"
sudo apt-get install -y git >/dev/null 2>&1

echo "> Ensuring Sqlite3 local database support"
sudo apt-get install -y sqlite3 libsqlite3-dev >/dev/null 2>&1

#install Python
./scripts/setup-python.sh

#install Docker and Docker Compose
./scripts/setup-docker.sh

#install Kubernetes CLI
./scripts/setup-kubernetes.sh

#Copy executable shortcuts
./scripts/link-commands.sh
