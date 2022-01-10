#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
HOME_DIR="$SCRIPT_DIR/.."

DOCKER_FILE="${1}"
#-------------------------------------------------------------------------------
echo "Ensuring project directories"
cd "$HOME_DIR"

mkdir -p lib
mkdir -p data
rm -f data/zimagi.env

echo "Initializing configuration"
if [ -z "$DOCKER_FILE" ]
then
    DOCKER_FILE="Dockerfile"
else
    DOCKER_FILE="Dockerfile.${DOCKER_FILE}"
fi

if [ ! -f .env ]
then
    cat > .env <<END
ZIMAGI_LOG_LEVEL=warning
ZIMAGI_SECRET_KEY=XXXXXX20181105
ZIMAGI_POSTGRES_DB=zimagi_db
ZIMAGI_POSTGRES_USER=zimagi_db_user
ZIMAGI_POSTGRES_PASSWORD=A1B3C5D7E9F10
ZIMAGI_REDIS_PASSWORD=A1B3C5D7E9F10
END
    env | grep "ZIMAGI_" >> .env || true
fi

echo "Ensuring certificates"
if [ ! -d certs ];
then
    ./scripts/fetch-certs.sh certs
fi
echo "Setting certificate environment"
export ZIMAGI_CA_KEY="$(cat certs/zimagi-ca.key)"
export ZIMAGI_CA_CERT="$(cat certs/zimagi-ca.crt)"
export ZIMAGI_KEY="$(cat certs/zimagi.key)"
export ZIMAGI_CERT="$(cat certs/zimagi.crt)"

echo "Setting encyption keys"
if [ -z "${ZIMAGI_DATA_KEY}" ];
then
    export ZIMAGI_DATA_KEY="$(cat certs/zimagi.crt)"
fi

echo "Package setup"
cp -f app/VERSION package/VERSION

echo "Building application"
docker build --force-rm --no-cache \
    --file "app/${DOCKER_FILE}" \
    --tag zimagi/zimagi:latest \
    --build-arg ZIMAGI_CA_KEY \
    --build-arg ZIMAGI_CA_CERT \
    --build-arg ZIMAGI_KEY \
    --build-arg ZIMAGI_CERT \
    --build-arg ZIMAGI_DATA_KEY \
    .
