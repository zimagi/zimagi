#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

LOG_FILE="/dev/stderr"
cd /usr/local/share/cenv

#-------------------------------------------------------------------------------

if [ ! -z "$POSTGRES_HOST" -a ! -z "$POSTGRES_PORT" ]
then
  ./scripts/wait.sh --host="$POSTGRES_HOST" --port="$POSTGRES_PORT"
fi

echo "> Migrating Django database structure" | tee -a "$LOG_FILE"
ce migrate --noinput >>"$LOG_FILE" 2>&1

echo "> Initializing application state" | tee -a "$LOG_FILE"
ce env get >>"$LOG_FILE" 2>&1

echo "> Starting application" | tee -a "$LOG_FILE"
gunicorn services.api.wsgi:application \
  --cert-reqs=1 \
  --ssl-version=2 \
  --certfile=/etc/ssl/certs/cenv.crt \
  --keyfile=/etc/ssl/private/cenv.key \
  --limit-request-field_size=0 \
  --limit-request-line=0 \
  --timeout 14400 \
  --worker-class=gevent \
  --workers=4 \
  --threads=12 \
  --worker-connections=100 \
  --bind=0.0.0.0:5123
