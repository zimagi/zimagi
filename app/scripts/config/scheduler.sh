export ZIMAGI_SERVICE_PROCESS=(
  "celery"
  "--app=settings"
  "beat"
  "--scheduler=systems.celery.scheduler:CeleryScheduler"
  "--loglevel=${ZIMAGI_LOG_LEVEL:-warning}"
  "--pidfile=/var/local/zimagi/scheduler.pid"
)
