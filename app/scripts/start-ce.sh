#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e
cd /usr/local/share/cenv
#-------------------------------------------------------------------------------

if [ ! -z "$POSTGRES_HOST" -a ! -z "$POSTGRES_PORT" ]
then
  ./scripts/wait.sh --host="$POSTGRES_HOST" --port="$POSTGRES_PORT"
fi

echo "> Initializing application"
ce module init --server --verbosity=3

echo "> Migrating database"
ce migrate --noinput

echo "> Environment information"
ce env get

echo "> Starting application"
gunicorn services.api.wsgi:application \
  --cert-reqs=1 \
  --ssl-version=2 \
  --certfile=/etc/ssl/certs/cenv.crt \
  --keyfile=/etc/ssl/private/cenv.key \
  --limit-request-field_size=0 \
  --limit-request-line=0 \
  --timeout=14400 \
  --worker-class=gevent \
  --workers=4 \
  --threads=12 \
  --worker-connections=100 \
  --bind=0.0.0.0:5123
