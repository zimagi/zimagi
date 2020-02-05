#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e
cd /usr/local/share/mcmi

export MCMI_WORKER_INIT=True
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

echo "> Initializing worker runtime"
mcmi module init --verbosity=3

echo "> Fetching environment information"
mcmi env get

echo "> Starting worker"
export MCMI_WORKER_EXEC=True

celery --app=services.tasks worker \
  --loglevel="$MCMI_LOG_LEVEL" \
  --concurrency="$MCMI_WORKER_CONCURRENCY"
