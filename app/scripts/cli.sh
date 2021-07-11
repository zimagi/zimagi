#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e
cd /usr/local/share/zimagi

export ZIMAGI_CLI_EXEC=True
#-------------------------------------------------------------------------------

# Execute CLI command
./zimagi.py "$@"