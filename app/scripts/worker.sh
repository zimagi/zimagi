#!/bin/bash --login
#-------------------------------------------------------------------------------
set -e
cd /usr/local/share/zimagi

export ZIMAGI_SERVICE=tasks
export ZIMAGI_WORKER_INIT=True
export ZIMAGI_NO_MIGRATE=True
export ZIMAGI_INIT_TIMEOUT="${ZIMAGI_INIT_TIMEOUT:-600}"
export ZIMAGI_WORKER_MIN_PROCESSES="${ZIMAGI_WORKER_MIN_PROCESSES:-10}"
export ZIMAGI_WORKER_MAX_PROCESSES="${ZIMAGI_WORKER_MAX_PROCESSES:-100}"
#-------------------------------------------------------------------------------

if [ ! -z "$ZIMAGI_POSTGRES_HOST" -a ! -z "$ZIMAGI_POSTGRES_PORT" ]; then
  ./scripts/wait.sh --hosts="$ZIMAGI_POSTGRES_HOST" --port="$ZIMAGI_POSTGRES_PORT" --timeout=60
fi
if [ ! -z "$ZIMAGI_REDIS_HOST" -a ! -z "$ZIMAGI_REDIS_PORT" ]; then
  ./scripts/wait.sh --hosts="$ZIMAGI_REDIS_HOST" --port="$ZIMAGI_REDIS_PORT" --timeout=60
fi

echo "> Initializing worker runtime"
zimagi module init --verbosity=3 --timeout="$ZIMAGI_INIT_TIMEOUT"

echo "> Fetching environment information"
zimagi env get

echo "> Starting worker"
export ZIMAGI_BOOTSTRAP_DJANGO=True
export ZIMAGI_WORKER_EXEC=True

WORKER_ARGS=(
  "--app=settings"
  "worker"
  "--loglevel=${ZIMAGI_LOG_LEVEL:-warning}"
  "--autoscale=${ZIMAGI_WORKER_MAX_PROCESSES},${ZIMAGI_WORKER_MIN_PROCESSES}"
)
if [ "${ZIMAGI_DEBUG^^}" == "TRUE" ]; then
  echo "> Starting file watcher (debug mode)"
  watchmedo auto-restart \
    --directory=./ \
    --pattern="*.py" \
    --recursive \
    -- celery "${WORKER_ARGS[@]}"
else
  celery "${WORKER_ARGS[@]}"
fi
