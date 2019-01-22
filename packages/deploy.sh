#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR"
#-------------------------------------------------------------------------------

STATUS=0

for filename in *
do
    if [ "$filename" != "shared" -a "$filename" != *"."* ]
    then
        echo "Deploying ${filename} package"
        "$filename/deploy.sh" &
    fi
done

for job in `jobs -p`
do
    wait $job || let "STATUS+=1"
done
exit $STATUS