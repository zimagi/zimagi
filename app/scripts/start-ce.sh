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

echo "> Clearing outdated locks" | tee -a "$LOG_FILE"
ce clear_locks >>"$LOG_FILE" 2>&1

echo "> Initializing application state" | tee -a "$LOG_FILE"
ce load --local >>"$LOG_FILE" 2>&1

echo "> Starting application" | tee -a "$LOG_FILE"
gunicorn services.api.wsgi:application \
  --cert-reqs=1 \
  --ssl-version=2 \
  --certfile=/etc/ssl/certs/cenv.crt \
  --keyfile=/etc/ssl/private/cenv.key \
  --worker-class=gevent \
  --workers=4 \
  --threads=12 \
  --worker-connections=100 \
  --bind=0.0.0.0:5123
