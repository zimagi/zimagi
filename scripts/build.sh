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
ZIMAGI_SECRET_KEY=XXXXXX20181105
ZIMAGI_POSTGRES_DB=zimagi_db
ZIMAGI_POSTGRES_USER=zimagi_db_user
ZIMAGI_POSTGRES_PASSWORD=A1B3C5D7E9F10
ZIMAGI_REDIS_PASSWORD=A1B3C5D7E9F10
END
    env | grep "ZIMAGI_" >> "${HOME_DIR}/.env" || true
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

echo "Setting encyption keys"
if [ -z "${ZIMAGI_DATA_KEY}" ];
then
    export ZIMAGI_DATA_KEY="$(cat "${HOME_DIR}/certs/zimagi.crt")"
fi

echo "Package setup"
cp -f "${HOME_DIR}/app/VERSION" "${HOME_DIR}/package/VERSION"

echo "Building application"
docker-compose -f "${HOME_DIR}/docker-compose.yml" build
