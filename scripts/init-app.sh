#!/usr/bin/env bash
# Prepare a Django database for application hosting.

set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/../app"

LOG_FILE="${1:-$SCRIPT_DIR/../logs/init.log}"
if [ "$LOG_FILE" != "/dev/stdout" -a "$LOG_FILE" != "/dev/stderr" ]
then
  rm -f "$LOG_FILE"
fi

#run application setup commands

echo "> Migrating Django database structure" | tee -a "$LOG_FILE"
./ce migrate --noinput >>"$LOG_FILE" 2>&1

echo "> Clearing outdated locks" | tee -a "$LOG_FILE"
./ce clear_locks >>"$LOG_FILE" 2>&1
