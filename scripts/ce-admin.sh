#!/usr/bin/env bash
#-------------------------------------------------------------------------------

if [ ! -z "$POSTGRES_HOST" -a ! -z "$POSTGRES_PORT" ]
then
    docker run --interactive --tty \
        --env LOGLEVEL \
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
        --env LOGLEVEL \
        --env-file /opt/cenv/config/core \
        --network host \
        --volume /opt/cenv/app:/usr/local/share/cenv \
        --volume /var/local/cenv:/var/local/cenv \
        cenv "$@"
fi
