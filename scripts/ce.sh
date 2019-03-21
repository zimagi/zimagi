#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

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

if [ -z "${CENV_DEBUG}" -o ! -z "${CENV_NO_SYNC}" ]
then
    echo " ** synchronizing runtime..."
    docker pull "${CENV_REMOTE}" >/dev/null 2>&1
fi
docker run --rm --interactive --tty \
    --env-file /var/local/cenv/django.env \
    --env-file /var/local/cenv/pg.credentials.env \
    --env-file <(env | grep "CENV_") \
    --network host \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    --volume /usr/local/share/cenv:/usr/local/share/cenv \
    --volume /var/local/cenv:/var/local/cenv \
    --volume /usr/local/lib/cenv:/usr/local/lib/cenv \
    "${CENV_IMAGE}" "${@}"
