#!/bin/bash --login
#-------------------------------------------------------------------------------
if [[ "${ZIMAGI_AUTO_UPDATE^^}" == "TRUE" ]]; then
  echo "> Starting file watcher"
  watchmedo auto-restart \
    --directory=./ \
    --directory=/usr/local/lib/zimagi \
    --pattern="*.py;*.sh" \
    --recursive \
    --signal SIGTERM \
    -- zimagi-gateway scheduler tasks
else
  zimagi-gateway scheduler tasks
fi
