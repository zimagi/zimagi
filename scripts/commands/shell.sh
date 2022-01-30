#
#=========================================================================================
# <Shell> Command
#

function shell_usage () {
    cat <<EOF >&2

Open a terminal session to a cluster Kubernetes pod within the Zimagi development environment.

Usage:

  reactor shell [<service:prompt>] [flags] [options]

Flags:
${__zimagi_reactor_core_flags}

EOF
  exit 1
}
function shell () {
  ZIMAGI_SERVICE=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
      shell_usage
      ;;
      *)
      if [[ "$1" == "-"* ]] || ! [ -z "$ZIMAGI_SERVICE" ]; then
        error "Unknown argument: ${1}"
        shell_usage
      fi
      ZIMAGI_SERVICE="${1}"
      ;;
    esac
    shift
  done

  debug "Command: shell"
  debug "> ZIMAGI_SERVICE: ${ZIMAGI_SERVICE}"

  start_zimagi_session "$ZIMAGI_SERVICE"
}
