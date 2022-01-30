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
function reload () {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
      reload_usage
      ;;
      *)
      error "Unknown argument: ${1}"
      reload_usage
      ;;
    esac
    shift
  done

  debug "Command: reload"

  reload_zimagi
}
