#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e
cd /usr/local/share/zimagi

export ZIMAGI_SERVICE=data
export ZIMAGI_COMMAND_PORT="${ZIMAGI_COMMAND_PORT:-5123}"
export ZIMAGI_DATA_PORT="${ZIMAGI_DATA_PORT:-5323}"
export ZIMAGI_API_INIT=True
export ZIMAGI_NO_MIGRATE=True
#-------------------------------------------------------------------------------

if [ ! -z "$ZIMAGI_POSTGRES_HOST" -a ! -z "$ZIMAGI_POSTGRES_PORT" ]
then
  ./scripts/wait.sh --hosts="$ZIMAGI_POSTGRES_HOST" --port="$ZIMAGI_POSTGRES_PORT" --timeout=60
fi
if [ ! -z "$ZIMAGI_REDIS_HOST" -a ! -z "$ZIMAGI_REDIS_PORT" ]
then
  ./scripts/wait.sh --hosts="$ZIMAGI_REDIS_HOST" --port="$ZIMAGI_REDIS_PORT" --timeout=60
fi

echo "> Initializing API runtime"
sleep 30
zimagi module init --verbosity=3

echo "> Fetching data environment information"
zimagi env get

echo "> Starting API"
export ZIMAGI_API_EXEC=True

gunicorn services.wsgi:application \
  --cert-reqs=1 \
  --ssl-version=2 \
  --certfile=/etc/ssl/certs/zimagi.crt \
  --keyfile=/etc/ssl/private/zimagi.key \
  --limit-request-field_size=0 \
  --limit-request-line=0 \
  --timeout=14400 \
  --worker-class=gevent \
  --workers=4 \
  --threads=12 \
  --worker-connections=100 \
  --bind="0.0.0.0:${ZIMAGI_DATA_PORT}"
