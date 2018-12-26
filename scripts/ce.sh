#!/usr/bin/env bash
#-------------------------------------------------------------------------------
docker run --interactive --tty \
    --env-file /opt/cenv/config/core \
    --network host \
    --volume /opt/cenv/app:/usr/local/share/cenv \
    --volume /var/local/cenv:/var/local/cenv \
    cenv "$@"
