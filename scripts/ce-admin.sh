#!/usr/bin/env bash
#-------------------------------------------------------------------------------
docker run --interactive --tty \
    --env LOGLEVEL \
    --env "POSTGRES_HOST=localhost" \
    --env "POSTGRES_PORT=5432" \
    --env-file /opt/cenv/config/core \
    --env-file /opt/cenv/config/pg.credentials \
    --network host \
    --volume /opt/cenv/app:/usr/local/share/cenv \
    --volume /var/local/cenv:/var/local/cenv \
    cenv "$@"
