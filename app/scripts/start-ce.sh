#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

LOG_FILE="/dev/stderr"
cd /usr/local/share/cenv

#-------------------------------------------------------------------------------

echo "> Migrating Django database structure" | tee -a "$LOG_FILE"
ce migrate --noinput >>"$LOG_FILE" 2>&1

echo "> Clearing outdated locks" | tee -a "$LOG_FILE"
ce clear_locks >>"$LOG_FILE" 2>&1

echo "> Starting application" | tee -a "$LOG_FILE"
gunicorn \
  --cert-reqs 2 \
  --ssl-version 2 \
  --do-handshake-on-connect True \
  --ca-certs /etc/ssl/certs/cenv-ca.crt \
  --certfile /etc/ssl/certs/cenv.crt \
  --keyfile /etc/ssl/private/cenv.key \
  -k gevent \
  -w 4 \
  --threads 12 \
  --worker-connections 100 \
  -b 0.0.0.0:5123 \
  services.api.wsgi:application
