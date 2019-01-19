#!/usr/bin/env bash
#-------------------------------------------------------------------------------

if [ -z "$TIME_ZONE" ]
then
    export TIME_ZONE="EST"
fi

if [ -f /var/local/cenv/cenv.env ]
then
    source /var/local/cenv/cenv.env

    CENV_ENV=`echo "${CENV_ENV}" | tr a-z A-Z`
    CENV_REPO=$(eval echo "\$${CENV_ENV}_REPO")
    CENV_IMAGE=$(eval echo "\$${CENV_ENV}_IMAGE")
else
    CENV_REPO=''
    CENV_IMAGE='cenv/cenv:latest'
fi

if [ ! -z "${CENV_REPO}" ]
then
    CENV_REMOTE="${CENV_REPO}/${CENV_IMAGE}"
else
    CENV_REMOTE="${CENV_IMAGE}"
fi
if [ -z "${DEBUG}" -o "${CENV_IMAGE}" != 'cenv/cenv:latest' ]
then
    echo " ** synchronizing runtime..."
    docker pull "${CENV_REMOTE}" >/dev/null 2>&1
fi

docker run --interactive --tty \
    --env LOG_LEVEL \
    --env DEBUG \
    --env TIME_ZONE \
    --env "POSTGRES_HOST=localhost" \
    --env "POSTGRES_PORT=5432" \
    --env-file /opt/cenv/data/django.env \
    --env-file /opt/cenv/data/pg.credentials.env \
    --network host \
    --volume /opt/cenv/app:/usr/local/share/cenv \
    --volume /var/local/cenv:/var/local/cenv \
    "${CENV_IMAGE}" "${@}"
