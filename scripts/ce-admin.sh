#!/usr/bin/env bash
#-------------------------------------------------------------------------------

if [ ! -z "$USE_POSTGRES" ]
then
    docker run --interactive --tty \
        --env "USE_POSTGRES=true" \
        --env "POSTGRES_HOST=$POSTGRES_HOST" \
        --env "POSTGRES_PORT=$POSTGRES_PORT" \
        --env-file /opt/cenv/config/core \
        --env-file /opt/cenv/config/pg.credentials \
        --network host \
        --volume /opt/cenv/app:/usr/local/share/cenv \
        --volume /var/local/cenv:/var/local/cenv \
        cenv "$@"    
else
    docker run --interactive --tty \
        --env-file /opt/cenv/config/core \
        --network host \
        --volume /opt/cenv/app:/usr/local/share/cenv \
        --volume /var/local/cenv:/var/local/cenv \
        cenv "$@"
fi
