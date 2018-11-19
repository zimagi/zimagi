#!/usr/bin/env bash
# Run a manage.py command from the app directory.

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/../app"

# Run manage.py from the app directory, regardless of where this run command was called
./hcp cli "$@"