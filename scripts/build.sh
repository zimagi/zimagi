#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
HOME_DIR="$SCRIPT_DIR/.."
#-------------------------------------------------------------------------------
echo "Ensuring project directories"
mkdir -p "${HOME_DIR}/data"
mkdir -p "${HOME_DIR}/lib"

echo "Initializing configuration"
if [ ! -f "${HOME_DIR}/.env" ]
then
    cat > "${HOME_DIR}/.env" <<END
ZIMAGI_LOG_LEVEL=warning
ZIMAGI_SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1)
ZIMAGI_POSTGRES_DB=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
ZIMAGI_POSTGRES_USER=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
ZIMAGI_POSTGRES_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
ZIMAGI_REDIS_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 20 | head -n 1)
END
    env | grep "ZIMAGI_" > "${HOME_DIR}/.env" || true
fi

echo "Ensuring certificates"
if [ ! -d "${HOME_DIR}/certs" ];
then
    "${HOME_DIR}/scripts/fetch-certs.sh" "${HOME_DIR}/certs"
fi

echo "Setting certificate environment"
export ZIMAGI_CA_KEY="$(cat "${HOME_DIR}/certs/zimagi-ca.key")"
export ZIMAGI_CA_CERT="$(cat "${HOME_DIR}/certs/zimagi-ca.crt")"
export ZIMAGI_KEY="$(cat "${HOME_DIR}/certs/zimagi.key")"
export ZIMAGI_CERT="$(cat "${HOME_DIR}/certs/zimagi.crt")"

echo "Building application"
docker-compose -f "${HOME_DIR}/docker-compose.yml" build
