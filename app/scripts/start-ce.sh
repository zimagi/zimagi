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
gunicorn services.api.wsgi:application \
  --cert-reqs=2 \
  --ssl-version=2 \
  --do-handshake-on-connect \
  --ca-certs=/etc/ssl/certs/cenv-ca.crt \
  --certfile=/etc/ssl/certs/cenv.crt \
  --keyfile=/etc/ssl/private/cenv.key \
  --worker-class=gevent \
  --workers=4 \
  --threads=12 \
  --worker-connections=100 \
  --bind=0.0.0.0:5123
