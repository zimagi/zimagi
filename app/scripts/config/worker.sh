export ZIMAGI_BOOTSTRAP_DJANGO=True
export ZIMAGI_SERVICE_PROCESS=(
  "celery"
  "--app=settings"
  "worker"
  "--loglevel=${ZIMAGI_LOG_LEVEL:-warning}"
  "--autoscale=${ZIMAGI_WORKER_MAX_PROCESSES:-10},${ZIMAGI_WORKER_MIN_PROCESSES:-1}"
)
