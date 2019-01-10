#!/usr/bin/env bash
#-------------------------------------------------------------------------------

if [ -z "$TIME_ZONE" ]
then
    export TIME_ZONE="EST"
fi

docker run --interactive --tty \
    --env LOG_LEVEL \
    --env DEBUG \
    --env TIME_ZONE \
    --env-file /opt/cenv/data/django.env \
    --network host \
    --volume /opt/cenv/app:/usr/local/share/cenv \
    --volume /var/local/cenv:/var/local/cenv \
    cenv "$@"
