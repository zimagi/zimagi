#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e
cd /usr/local/share/mcmi

export MCMI_API_INIT=True
#-------------------------------------------------------------------------------

if [ ! -z "$MCMI_POSTGRES_HOST" -a ! -z "$MCMI_POSTGRES_PORT" ]
then
  ./scripts/wait.sh --hosts="$MCMI_POSTGRES_HOST" --port="$MCMI_POSTGRES_PORT"
fi

echo "> Initializing application"
mcmi module init --verbosity=3
mcmi run core display
mcmi env get

echo "> Starting application"
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
  --bind=0.0.0.0:5123
