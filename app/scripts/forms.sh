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
    --debug-force-polling \
    --interval 1 \
    -- zimagi-gateway wsgi_ui forms
else
  zimagi-gateway wsgi_ui forms
fi
