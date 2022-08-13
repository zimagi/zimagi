#!/bin/bash --login
#-------------------------------------------------------------------------------
if [[ "${ZIMAGI_AUTO_UPDATE^^}" == "TRUE" ]]; then
  echo "> Starting file watcher"
  watchmedo auto-restart \
    --directory=./ \
    --directory=/usr/local/lib/zimagi/modules \
    --pattern="*.py;*.sh" \
    --recursive \
    --signal SIGTERM \
    --debug-force-polling \
    --interval 1 \
    -- zimagi-gateway worker tasks
else
  zimagi-gateway worker tasks
fi
