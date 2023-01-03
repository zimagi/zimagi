export ZIMAGI_STARTUP_SERVICES='[]'
export ZIMAGI_BOOTSTRAP_DJANGO=True
export ZIMAGI_QUEUE_COMMANDS=True

WORKER_QUEUES="default"
if [ ! -z "$ZIMAGI_WORKER_TYPE" ]; then
  WORKER_QUEUES="${ZIMAGI_WORKER_TYPE},${WORKER_QUEUES}"
fi

export ZIMAGI_SERVICE_PROCESS=(
  "celery"
  "--app=settings"
  "worker"
  "--loglevel=${ZIMAGI_LOG_LEVEL:-info}"
  "--autoscale=${ZIMAGI_WORKER_MAX_PROCESSES:-10},${ZIMAGI_WORKER_MIN_PROCESSES:-1}"
  "--queues=${WORKER_QUEUES}"
)
