#!/bin/bash --login
#-------------------------------------------------------------------------------
export ZIMAGI_SERVICE=data
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
    -- zimagi-gateway api
else
  zimagi-gateway api
fi
