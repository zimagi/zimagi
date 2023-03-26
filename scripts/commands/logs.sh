#
#=========================================================================================
# <Logs> Command
#

function logs_usage () {
    cat <<EOF >&2

Display log entries for Zimagi services.

Usage:

  reactor logs [flags] [options] <service_name:str> ...

Flags:
${__zimagi_reactor_core_flags}

    --follow              Follow service logs entries over time
    --timestamps          Display timestamps for each log entry

Options:

    --tail <int>          Display the last N log entries: 100

EOF
  exit 1
}
function logs_command () {
  SERVICES=()
  LOGS_ARGS=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --tail=*)
      TAIL="${1#*=}"
      ;;
      --tail)
      TAIL="$2"
      shift
      ;;
      --follow)
      FOLLOW=1
      ;;
      --timestamps)
      TIMESTAMPS=1
      ;;
      -h|--help)
      logs_usage
      ;;
      *)
      SERVICES=("${SERVICES[@]}" "$1")
      ;;
    esac
    shift
  done
  TAIL="${TAIL:-100}"
  FOLLOW=${FOLLOW:-0}
  TIMESTAMPS=${TIMESTAMPS:-0}

  if [ -z "${SERVICES[*]}" ]; then
    SERVICES=("command-api" "data-api" "scheduler" "worker")
  fi

  SERVICE_NAMES=$(printf ",%s" "${SERVICES[@]}")
  SERVICE_NAMES="${SERVICE_NAMES:1}"

  LOGS_ARGS=(
    "${LOGS_ARGS[@]}"
    "--prefix"
    "--tail=${TAIL}"
    "-n" "zimagi"
    "-l" "app.kubernetes.io/component in (${SERVICE_NAMES})"
  )
  if [ $FOLLOW -ne 0 ]; then
    LOGS_ARGS=("${LOGS_ARGS[@]}" "--follow")
  fi
  if [ $TIMESTAMPS -ne 0 ]; then
    LOGS_ARGS=("${LOGS_ARGS[@]}" "--timestamps")
  fi

  debug "Command: logs"
  debug "> SERVICES: ${SERVICES[@]}"
  debug "> SERVICE_NAMES: ${SERVICE_NAMES}"
  debug "> TAIL: ${TAIL}"
  debug "> FOLLOW: ${FOLLOW}"
  debug "> TIMESTAMPS: ${TIMESTAMPS}"
  debug "> LOGS_ARGS: ${LOGS_ARGS[@]}"

  "${__zimagi_binary_dir}/kubectl" logs "${LOGS_ARGS[@]}"
}
