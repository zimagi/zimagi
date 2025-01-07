export ZIMAGI_SERVICE_PROCESS=(
  "celery"
  "--app=settings"
  "beat"
  "--scheduler=systems.celery.scheduler:CeleryScheduler"
  "--loglevel=${ZIMAGI_LOG_LEVEL:-info}"
  "--pidfile=/var/local/zimagi/scheduler.pid"
)
