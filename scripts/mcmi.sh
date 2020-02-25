#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

DEFAULT_MCMI_IMAGE="${DEFAULT_MCMI_IMAGE:-mcmi/mcmi:latest}"

if [ -f /var/local/mcmi/mcmi.env ]
then
    source /var/local/mcmi/mcmi.env
else
    MCMI_REPO=''
    MCMI_IMAGE="${DEFAULT_MCMI_IMAGE}"
fi

if ! docker inspect "${MCMI_IMAGE}" >/dev/null 2>&1
then
    rm -f /var/local/mcmi/mcmi.env
    MCMI_IMAGE="${DEFAULT_MCMI_IMAGE}"
fi
docker run --rm --interactive --tty \
    --env "MCMI_CLI_EXEC=True" \
    --env-file /var/local/mcmi/.env \
    --env-file <(env | grep "MCMI_") \
    --network host \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    --volume /usr/local/share/mcmi:/usr/local/share/mcmi \
    --volume /var/local/mcmi:/var/local/mcmi \
    --volume /usr/local/lib/mcmi:/usr/local/lib/mcmi \
    "${MCMI_IMAGE}" "${@}"
