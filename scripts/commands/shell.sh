#
#=========================================================================================
# <Shell> Command
#

function shell_usage () {
    cat <<EOF >&2

Open a terminal session to a running Zimagi service

Usage:

  reactor shell [flags] [options] [<service_pod_name:str>]

Flags:
${__zimagi_reactor_core_flags}

EOF
  exit 1
}
function shell_command () {
  SERVICE_POD_NAME=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
      shell_usage
      ;;
      *)
      if [[ "$1" == "-"* ]] || ! [ -z "$SERVICE_POD_NAME" ]; then
        error "Unknown argument: ${1}"
        shell_usage
      fi
      SERVICE_POD_NAME="${1}"
      ;;
    esac
    shift
  done

  debug "Command: shell"
  debug "> SERVICE_POD_NAME: ${SERVICE_POD_NAME}"

  start_zimagi_session "$SERVICE_POD_NAME"
}
