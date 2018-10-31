#!/usr/bin/env bash
# Initialize a new cluster server (immediately after OS installation)

set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

BACKUP_DEVICE="${1:-/dev/sda3}"

#-------------------------------------------------------------------------------

# Upgrade core OS packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Timeshift
sudo add-apt-repository -y ppa:teejee2008/ppa
sudo apt-get update
sudo apt-get install -y timeshift
  
# Create system restore point
sudo timeshift --create --scripted --yes --rsync --snapshot-device "$BACKUP_DEVICE"
