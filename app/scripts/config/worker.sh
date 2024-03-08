export ZIMAGI_STARTUP_SERVICES='[]'
export ZIMAGI_QUEUE_COMMANDS=True

WORKER_QUEUE="default"
if [ ! -z "$ZIMAGI_WORKER_TYPE" ]; then
  WORKER_QUEUE="${ZIMAGI_WORKER_TYPE}"
fi

export ZIMAGI_SERVICE_PROCESS=(
  "celery"
  "--app=settings"
  "worker"
  "--task-events"
  "--optimization=fair"
  "--pool=processes"
  "--loglevel=${ZIMAGI_LOG_LEVEL:-info}"
  "--autoscale=${ZIMAGI_WORKER_MAX_PROCESSES:-10},${ZIMAGI_WORKER_MIN_PROCESSES:-1}"
  "--queues=${WORKER_QUEUE}"
)
