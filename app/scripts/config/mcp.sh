export ZIMAGI_SERVICE_PROCESS=(
  "uvicorn"
  "services.mcp:application"
  "--log-level=${ZIMAGI_LOG_LEVEL:-info}"
  "--timeout-keep-alive=${ZIMAGI_SERVER_TIMEOUT:-14400}"
  "--workers=1"
  "--limit-concurrency=${ZIMAGI_SERVER_CONNECTIONS:-100}"
  "--backlog=${ZIMAGI_SERVER_MAX_PENDING_CONNECTIONS:-3000}"
  "--host=0.0.0.0"
  "--port=5000"
)
