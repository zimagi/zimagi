#!/bin/bash --login
#-------------------------------------------------------------------------------
set -e
cd /usr/local/share/zimagi

export ZIMAGI_DEBUG=True
export ZIMAGI_DISPLAY_COLOR=False
#-------------------------------------------------------------------------------

# Execute module install
./zimagi-install.py "$@"
