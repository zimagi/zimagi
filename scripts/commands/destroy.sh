#
#=========================================================================================
# <Destroy> Command
#

function destroy_usage () {
    cat <<EOF >&2

Shut down and destroy Zimagi development environment.

Usage:

  reactor destroy [flags] [options]

Flags:
${__core_help_flags}

EOF
  exit 1
}
function destroy () {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
      destroy_usage
      ;;
      *)
      error "Unknown argument: ${1}"
      destroy_usage
      ;;
    esac
    shift
  done

  debug "Command: destroy"

  destroy_minikube

  info "Zimagi development environment has been destroyed"
}
