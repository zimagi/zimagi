#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

LOG_FILE="/dev/stderr"
SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/../app"

#-------------------------------------------------------------------------------

echo "> Migrating Django database structure" | tee -a "$LOG_FILE"
./ce migrate --noinput >>"$LOG_FILE" 2>&1

echo "> Clearing outdated locks" | tee -a "$LOG_FILE"
./ce clear_locks >>"$LOG_FILE" 2>&1

echo "> Starting application" | tee -a "$LOG_FILE"
gunicorn \
  --cert-reqs 2 \
  --ssl-version 2 \
  --do-handshake-on-connect True \
  --ca_certs /etc/ssl/certs/cenv-ca.crt \
  --certfile /etc/ssl/certs/cenv.crt \
  --keyfile /etc/ssl/private/cenv.key \
  -k gevent \
  -w 4 \
  --threads 12 \
  --worker-connections 100 \
  -b 0.0.0.0:5120 \
  services.api.wsgi:application
