export ZIMAGI_SERVICE_PROCESS=(
  "gunicorn"
  "services.wsgi:application"
  "--limit-request-field_size=0"
  "--limit-request-fields=0"
  "--limit-request-line=0"
  "--log-level=${ZIMAGI_LOG_LEVEL:-info}"
  "--access-logformat=[gunicorn] %(h)s '%(t)s' %(U)s '%(q)s' %(s)s %(b)s '%(f)s' '%(a)s'"
  "--access-logfile=-" # STDOUT
  "--error-logfile=-" # STDERR
  "--timeout=${ZIMAGI_SERVER_TIMEOUT:-14400}"
  "--worker-class=gevent"
  "--workers=${ZIMAGI_SERVER_WORKERS:-4}"
  "--worker-connections=${ZIMAGI_SERVER_CONNECTIONS:-100}"
  "--backlog=${ZIMAGI_SERVER_MAX_PENDING_CONNECTIONS:-3000}"
  "--bind=0.0.0.0:5000"
)
