#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

DEFAULT_CENV_IMAGE='cenv/cenv:latest'

if [ -f /var/local/cenv/cenv.env ]
then
    source /var/local/cenv/cenv.env
else
    CENV_REPO=''
    CENV_IMAGE="${DEFAULT_CENV_IMAGE}"
fi

function sync_image() {
    IMAGE="$1"

    if [ ! -z "${CENV_REPO}" ]
    then
        CENV_REMOTE="${CENV_REPO}/${IMAGE}"
    else
        CENV_REMOTE="${IMAGE}"
    fi

    if [ -z "${CENV_DEBUG}" -o ! -z "${CENV_NO_SYNC}" ]
    then
        echo " ** synchronizing runtime..."
        docker pull "${CENV_REMOTE}" >/dev/null 2>&1
    fi
    echo "$IMAGE"
}

CENV_IMAGE="$(sync_image ${CENV_IMAGE})"
if ! docker inspect "${CENV_IMAGE}" >/dev/null 2>&1
then
    rm -f /var/local/cenv/cenv.env
    CENV_IMAGE="$(sync_image ${DEFAULT_CENV_IMAGE})"
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
