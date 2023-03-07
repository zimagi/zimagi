#
#=========================================================================================
# <Reload> Command
#

function reload_usage () {
    cat <<EOF >&2

Reload Zimagi development environment services.

Usage:

  reactor reload [flags] [options]

Flags:
${__zimagi_reactor_core_flags}

EOF
  exit 1
}
function reload_command () {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
      reload_usage
      ;;
      *)
      if ! [ -z "$1" ]; then
        error "Unknown argument: ${1}"
        reload_usage
      fi
      ;;
    esac
    shift
  done

  debug "Command: reload"

  reload_zimagi
}
