#!/bin/bash --login
#-------------------------------------------------------------------------------
set -e
cd /usr/local/share/zimagi

export ZIMAGI_SERVICE=tasks
export ZIMAGI_SCHEDULER_INIT=True
export ZIMAGI_NO_MIGRATE=True
export ZIMAGI_INIT_TIMEOUT="${ZIMAGI_INIT_TIMEOUT:-600}"
#-------------------------------------------------------------------------------

if [ ! -z "$ZIMAGI_POSTGRES_HOST" -a ! -z "$ZIMAGI_POSTGRES_PORT" ]; then
  ./scripts/wait.sh --hosts="$ZIMAGI_POSTGRES_HOST" --port="$ZIMAGI_POSTGRES_PORT" --timeout=60
fi
if [ ! -z "$ZIMAGI_REDIS_HOST" -a ! -z "$ZIMAGI_REDIS_PORT" ]; then
  ./scripts/wait.sh --hosts="$ZIMAGI_REDIS_HOST" --port="$ZIMAGI_REDIS_PORT" --timeout=60
fi

echo "> Initializing scheduler runtime"
zimagi migrate
zimagi module init --verbosity=3 --timeout="$ZIMAGI_INIT_TIMEOUT"

if [ ! -z "$ZIMAGI_TEST_KEY" ]; then
    zimagi user save admin encryption_key="$ZIMAGI_TEST_KEY"
fi

echo "> Fetching environment information"
zimagi env get

if ! zimagi state get initialized >/dev/null 2>&1; then
  zimagi user get admin
fi
zimagi state save initialized value=True >/dev/null 2>&1

echo "> Starting scheduler"
export ZIMAGI_BOOTSTRAP_DJANGO=True
export ZIMAGI_SCHEDULER_EXEC=True

rm -f /var/local/zimagi/celerybeat.pid

SCHEDULER_ARGS=(
  "--app=settings"
  "beat"
  "--scheduler=systems.celery.scheduler:CeleryScheduler"
  "--loglevel=${ZIMAGI_LOG_LEVEL:-warning}"
  "--pidfile=/var/local/zimagi/celerybeat.pid"
)

if [ "${ZIMAGI_DEBUG^^}" == "TRUE" ]; then
  watchmedo auto-restart \
    --directory=./ \
    --pattern="*.py" \
    --recursive \
    -- celery "${SCHEDULER_ARGS[@]}"
else
  celery "${SCHEDULER_ARGS[@]}"
fi
