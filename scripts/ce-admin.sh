#!/usr/bin/env bash
#-------------------------------------------------------------------------------

if [ -z "$TIME_ZONE" ]
then
    export TIME_ZONE="EST"
fi

if [ -f /var/local/cenv/cenv.env ]
then
    source /var/local/cenv/cenv.env
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

if [ -z "${DEBUG}" ]
then
    echo " ** synchronizing runtime..."
    docker pull "${CENV_REMOTE}" >/dev/null 2>&1
fi
docker run --interactive --tty \
    --env LOG_LEVEL \
    --env DEBUG \
    --env TIME_ZONE \
    --env DATA_ENCRYPT \
    --env "POSTGRES_HOST=localhost" \
    --env "POSTGRES_PORT=5432" \
    --env-file /var/local/cenv/django.env \
    --env-file /var/local/cenv/pg.credentials.env \
    --network host \
    --volume /usr/local/share/cenv:/usr/local/share/cenv \
    --volume /var/local/cenv:/var/local/cenv \
    --volume /usr/local/lib/cenv:/usr/local/lib/cenv \
    "${CENV_IMAGE}" "${@}"
