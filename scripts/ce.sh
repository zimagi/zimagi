#!/usr/bin/env bash
#-------------------------------------------------------------------------------
docker run \
    -v /opt/cenv/app:/usr/local/share/cenv \
    -v /var/local/cenv:/var/local/cenv \
    -it cenv "$@"
