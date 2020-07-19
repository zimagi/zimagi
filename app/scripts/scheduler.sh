#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e
cd /usr/local/share/zimagi

export ZIMAGI_SERVICE=tasks
export ZIMAGI_SCHEDULER_INIT=True
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

echo "> Initializing scheduler runtime"
sleep 90
zimagi module init --verbosity=3

echo "> Fetching environment information"
zimagi env get

echo "> Starting scheduler"
export ZIMAGI_BOOTSTRAP_DJANGO=True
export ZIMAGI_SCHEDULER_EXEC=True

rm -f /var/local/zimagi/celerybeat.pid

celery --app=settings beat \
  --scheduler=systems.celery.scheduler:CeleryScheduler \
  --loglevel="$ZIMAGI_LOG_LEVEL" \
  --pidfile=/var/local/zimagi/celerybeat.pid
