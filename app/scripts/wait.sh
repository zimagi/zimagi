#!/usr/bin/env bash
#
#   Use this script to test if a given TCP host/port are available
#
# Derived from: https://github.com/vishnubob/wait-for-it
# Licenced under: MIT License
#
cmdname=$(basename $0)

echoerr() {
    if [[ $QUIET -ne 1 ]]
    then
        echo "$@" 1>&2
    fi
}

usage() {
    cat << USAGE >&2
Usage:
    $cmdname host [-s] [-t timeout]
    -h HOSTS   | --hosts=HOSTS     Comma separated hosts or IPs to test
    -p PORT    | --port=PORT       TCP port to test
    -q         | --quiet           Don't output any status messages
    -t TIMEOUT | --timeout=TIMEOUT Timeout in seconds, zero for no timeout
USAGE
    exit 1
}

wait_for() {
    host="$1"

    if [[ $TIMEOUT -gt 0 ]]
    then
        echoerr "$cmdname: waiting $TIMEOUT seconds for $host:$PORT"
    else
        echoerr "$cmdname: waiting for $host:$PORT without a timeout"
    fi

    start_ts=$(date +%s)
    while :
    do
        (echo > /dev/tcp/$host/$PORT) >/dev/null 2>&1
        result=$?

        if [[ $result -eq 0 ]]
        then
            end_ts=$(date +%s)
            echoerr "$cmdname: $host:$PORT is available after $((end_ts - start_ts)) seconds"
            break
        fi
        sleep 1
    done
    return $result
}

wait_for_wrapper() {
    host="$1"

    if [[ $QUIET -eq 1 ]]
    then
        timeout $TIMEOUT $0 --quiet --child --hosts=$host --port=$PORT --timeout=$TIMEOUT &
    else
        timeout $TIMEOUT $0 --child --hosts=$host --port=$PORT --timeout=$TIMEOUT &
    fi

    PID=$!
    trap "kill -INT -$PID" INT
    wait $PID
    RESULT=$?
    if [[ $RESULT -ne 0 ]]
    then
        echoerr "$cmdname: timeout occurred after waiting $TIMEOUT seconds for $host:$PORT"
    fi
    return $RESULT
}

while [[ $# -gt 0 ]]
do
    case "$1" in
        --child)
        CHILD=1
        shift 1
        ;;
        -q | --quiet)
        QUIET=1
        shift 1
        ;;
        -h)
        HOSTS="$2"
        if [[ $HOSTS == "" ]]; then break; fi
        shift 2
        ;;
        --hosts=*)
        HOSTS="${1#*=}"
        shift 1
        ;;
        -p)
        PORT="$2"
        if [[ $PORT == "" ]]; then break; fi
        shift 2
        ;;
        --port=*)
        PORT="${1#*=}"
        shift 1
        ;;
        -t)
        TIMEOUT="$2"
        if [[ $TIMEOUT == "" ]]; then break; fi
        shift 2
        ;;
        --timeout=*)
        TIMEOUT="${1#*=}"
        shift 1
        ;;
        --help)
        usage
        ;;
        *)
        echoerr "Unknown argument: $1"
        usage
        ;;
    esac
done

if [[ "$HOSTS" == "" || "$PORT" == "" ]]
then
    echoerr "Error: you need to provide a host and port to test."
    usage
fi

TIMEOUT=${TIMEOUT:-15}
CHILD=${CHILD:-0}
QUIET=${QUIET:-0}

IFS=',' read -r -a hosts <<< "$HOSTS"

for host in "${hosts[@]}"
do
    if [[ $CHILD -gt 0 ]]
    then
        wait_for "$host"
        RESULT=$?
    else
        if [[ $TIMEOUT -gt 0 ]]
        then
            wait_for_wrapper "$host"
            RESULT=$?
        else
            wait_for "$host"
            RESULT=$?
        fi
    fi
    if [[ $RESULT -ne 0 ]]
    then
        echoerr "$cmdname: timeout occurred after waiting $TIMEOUT seconds for $host:$PORT"
        exit $RESULT
    fi
done
exit $RESULT
