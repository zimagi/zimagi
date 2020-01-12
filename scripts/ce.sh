#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

DEFAULT_MCMI_IMAGE='mcmi/mcmi:latest'

if [ -f /var/local/mcmi/mcmi.env ]
then
    source /var/local/mcmi/mcmi.env
else
    MCMI_REPO=''
    MCMI_IMAGE="${DEFAULT_MCMI_IMAGE}"
fi

function sync_image() {
    IMAGE="$1"

    if [ ! -z "${MCMI_REPO}" ]
    then
        MCMI_REMOTE="${MCMI_REPO}/${IMAGE}"
    else
        MCMI_REMOTE="${IMAGE}"
    fi

    if [ -z "${MCMI_DEBUG}" -o ! -z "${MCMI_NO_SYNC}" ]
    then
        echo " ** synchronizing runtime..."
        docker pull "${MCMI_REMOTE}" >/dev/null 2>&1
    fi
    echo "$IMAGE"
}

MCMI_IMAGE="$(sync_image ${MCMI_IMAGE})"
if ! docker inspect "${MCMI_IMAGE}" >/dev/null 2>&1
then
    rm -f /var/local/mcmi/mcmi.env
    MCMI_IMAGE="$(sync_image ${DEFAULT_MCMI_IMAGE})"
fi
docker run --rm --interactive --tty \
    --env-file /var/local/mcmi/.env \
    --env-file <(env | grep "MCMI_") \
    --network host \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    --volume /usr/local/share/mcmi:/usr/local/share/mcmi \
    --volume /var/local/mcmi:/var/local/mcmi \
    --volume /usr/local/lib/mcmi:/usr/local/lib/mcmi \
    "${MCMI_IMAGE}" "${@}"
