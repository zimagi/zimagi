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
    $cmdname
    -h | --help         Display help information
    --hosts=HOSTS       Comma separated hosts or IPs to test
    --port=PORT         TCP port to test
    --http              Check for HTTP status 200, 301, or 302
    --https             Check for HTTPS status 200, 301, or 302
    --quiet             Don't output any status messages
    --timeout=TIMEOUT   Timeout in seconds, zero for no timeout
USAGE
    exit 1
}


while [[ $# -gt 0 ]]
do
    case "$1" in
        --child)
        CHILD=1
        shift 1
        ;;
        --http)
        HTTP_CHECK=1
        shift 1
        ;;
        --https)
        HTTPS_CHECK=1
        shift 1
        ;;
        --quiet)
        QUIET=1
        shift 1
        ;;
        --hosts=*)
        HOSTS="${1#*=}"
        shift 1
        ;;
        --port=*)
        PORT="${1#*=}"
        shift 1
        ;;
        --timeout=*)
        TIMEOUT="${1#*=}"
        shift 1
        ;;
        -h | --help)
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
HTTP_CHECK=${HTTP_CHECK:-0}
HTTPS_CHECK=${HTTPS_CHECK:-0}


wait_for() {
    host="$1"
    alive_status=("200" "301" "302")

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
            if [[ $HTTP_CHECK -eq 1 || $HTTPS_CHECK -eq 1 ]]
            then
                if [[ $HTTPS_CHECK -eq 1 ]]
                then
                    test_host="https://$host:$PORT"
                else
                    test_host="http://$host:$PORT"
                fi
                status="$(curl --head --write-out %{http_code} --silent --output /dev/null "$test_host")"
                if [[ ! "${alive_status[@]}" =~ "${status}" ]]
                then
                    continue
                fi
            fi
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
    cmdopts=( "--child" )

    if [[ $QUIET -eq 1 ]]
    then
        cmdopts+=( "--quiet" )
    fi
    if [[ $HTTP_CHECK -eq 1 ]]
    then
        cmdopts+=( "--http" )
    fi
    if [[ $HTTPS_CHECK -eq 1 ]]
    then
        cmdopts+=( "--https" )
    fi

    timeout $TIMEOUT $0 "${cmdopts[@]}" --hosts=$host --port=$PORT --timeout=$TIMEOUT &

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
