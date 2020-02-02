#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e
cd /usr/local/share/mcmi

export MCMI_SCHEDULER_INIT=True
#-------------------------------------------------------------------------------

if [ ! -z "$MCMI_POSTGRES_HOST" -a ! -z "$MCMI_POSTGRES_PORT" ]
then
  ./scripts/wait.sh --hosts="$MCMI_POSTGRES_HOST" --port="$MCMI_POSTGRES_PORT" --timeout=60
fi
if [ ! -z "$MCMI_REDIS_HOST" -a ! -z "$MCMI_REDIS_PORT" ]
then
  ./scripts/wait.sh --hosts="$MCMI_REDIS_HOST" --port="$MCMI_REDIS_PORT" --timeout=60
fi
if [ ! -z "$MCMI_API_HOST" -a ! -z "$MCMI_API_PORT" ]
then
  ./scripts/wait.sh --hosts="$MCMI_API_HOST" --port="$MCMI_API_PORT" --timeout=600
fi

echo "> Initializing scheduler runtime"
mcmi module init --verbosity=3
mcmi env get

echo "> Starting scheduler"
export MCMI_SCHEDULER_EXEC=True

rm -f /var/local/mcmi/celerybeat.pid

celery --app=services.tasks beat \
  --scheduler=systems.celery.scheduler:CeleryScheduler \
  --loglevel="$MCMI_LOG_LEVEL" \
  --pidfile=/var/local/mcmi/celerybeat.pid
