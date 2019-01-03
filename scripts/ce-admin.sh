#!/usr/bin/env bash
#-------------------------------------------------------------------------------

if [ -z "$TIME_ZONE" ]
then
    export TIME_ZONE="EST"
fi

docker run --interactive --tty \
    --env LOGLEVEL \
    --env DEBUG \
    --env TIME_ZONE \
    --env "POSTGRES_HOST=localhost" \
    --env "POSTGRES_PORT=5432" \
    --env-file /opt/cenv/config/django \
    --env-file /opt/cenv/config/pg.credentials \
    --network host \
    --volume /opt/cenv/app:/usr/local/share/cenv \
    --volume /var/local/cenv:/var/local/cenv \
    cenv "$@"
