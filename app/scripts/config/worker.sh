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
  "--pool=prefork"
  "--concurrency=1"
  "--max-tasks-per-child=${ZIMAGI_WORKER_TASKS_PER_PROCESS:-100}"
  "--loglevel=${ZIMAGI_LOG_LEVEL:-info}"
  "--queues=${WORKER_QUEUE}"
)
