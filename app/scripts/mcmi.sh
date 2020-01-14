#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e
cd /usr/local/share/mcmi

export MCMI_CLI_EXEC=True
#-------------------------------------------------------------------------------

# Execute CLI command
./mcmi.py "$@"