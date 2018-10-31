#!/usr/bin/env bash
# Restore an existing cluster server to previous point in time

set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

BACKUP_DEVICE="${1:-/dev/sda3}"
TARGET_DEVICE="${1:-/dev/sda2}"

#-------------------------------------------------------------------------------

# Restore system from restore point
sudo timeshift --restore --yes --rsync --skip-grub --snapshot-device "$BACKUP_DEVICE" --target-device "$TARGET_DEVICE"
