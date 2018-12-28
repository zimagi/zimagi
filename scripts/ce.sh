#!/usr/bin/env bash
#-------------------------------------------------------------------------------

if [ -z "$TIME_ZONE" ]
then
    export TIME_ZONE="EST"
fi

docker run --interactive --tty \
    --env LOGLEVEL \
    --env DEV_ENV \
    --env DEBUG \
    --env TIME_ZONE \
    --env-file /opt/cenv/config/django \
    --network host \
    --volume /opt/cenv/app:/usr/local/share/cenv \
    --volume /var/local/cenv:/var/local/cenv \
    cenv "$@"
