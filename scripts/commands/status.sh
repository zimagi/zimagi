#
#=========================================================================================
# <Status> Command
#

function status_usage () {
    cat <<EOF >&2

Check status of nodes and pods in the Zimagi development environment.

Usage:

  reactor status [flags] [options]

Flags:
${__zimagi_reactor_core_flags}

EOF
  exit 1
}
function status_command () {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
      status_usage
      ;;
      *)
      error "Unknown argument: ${1}"
      status_usage
      ;;
    esac
    shift
  done

  debug "Command: status"

  zimagi_status
}
