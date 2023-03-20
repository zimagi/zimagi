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
${__zimagi_reactor_core_flags}

EOF
  exit 1
}
function down_command () {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
      down_usage
      ;;
      *)
      if ! [ -z "$1" ]; then
        error "Unknown argument: ${1}"
        down_usage
      fi
      ;;
    esac
    shift
  done

  debug "Command: down"

  stop_minikube
  remove_dns_records

  info "Zimagi development environment has been shut down"
}
