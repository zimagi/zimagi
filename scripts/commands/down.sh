#
#=========================================================================================
# <Down> Command
#

function down_usage () {
    cat <<EOF >&2

Shut down but do not destroy Zimagi development environment services.

Usage:

  reactor down [flags] [options]

Flags:
${__core_help_flags}

EOF
  exit 1
}
function down () {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
      down_usage
      ;;
      *)
      error "Unknown argument: ${1}"
      down_usage
      ;;
    esac
    shift
  done

  debug "Command: down"

  stop_minikube

  info "Zimagi development environment has been shut down"
}
