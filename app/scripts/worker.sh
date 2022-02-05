#!/bin/bash --login
#-------------------------------------------------------------------------------
export ZIMAGI_SERVICE=tasks
#-------------------------------------------------------------------------------

if [[ "${ZIMAGI_AUTO_UPDATE^^}" == "TRUE" ]]; then
  echo "> Starting file watcher"
  watchmedo auto-restart \
    --directory=./ \
    --directory=/usr/local/lib/zimagi \
    --directory=/usr/local/share/zimagi-client \
    --pattern="*.py;*.sh" \
    --recursive \
    --signal SIGTERM \
    --kill-after ${ZIMAGI_RESTART_TIMEOUT:-86400} \
    -- zimagi-gateway worker
else
  zimagi-gateway worker
fi
