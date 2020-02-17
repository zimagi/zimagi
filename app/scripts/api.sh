#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e
cd /usr/local/share/mcmi

export MCMI_API_PORT="${MCMI_API_PORT:-5123}"
export MCMI_API_INIT=True
#-------------------------------------------------------------------------------

if [ ! -z "$MCMI_POSTGRES_HOST" -a ! -z "$MCMI_POSTGRES_PORT" ]
then
  ./scripts/wait.sh --hosts="$MCMI_POSTGRES_HOST" --port="$MCMI_POSTGRES_PORT" --timeout=60
fi
if [ ! -z "$MCMI_REDIS_HOST" -a ! -z "$MCMI_REDIS_PORT" ]
then
  ./scripts/wait.sh --hosts="$MCMI_REDIS_HOST" --port="$MCMI_REDIS_PORT" --timeout=60
fi

echo "> Initializing API runtime"
sleep $((RANDOM % 20))
mcmi module init --verbosity=3

echo "> Fetching environment information"
mcmi env get

echo "> Starting API"
export MCMI_API_EXEC=True

gunicorn services.api.wsgi:application \
  --cert-reqs=1 \
  --ssl-version=2 \
  --certfile=/etc/ssl/certs/mcmi.crt \
  --keyfile=/etc/ssl/private/mcmi.key \
  --limit-request-field_size=0 \
  --limit-request-line=0 \
  --timeout=14400 \
  --worker-class=gevent \
  --workers=4 \
  --threads=12 \
  --worker-connections=100 \
  --bind="0.0.0.0:${MCMI_API_PORT}"
