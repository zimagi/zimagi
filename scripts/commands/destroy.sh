#
#=========================================================================================
# <Destroy> Command
#

function destroy_usage () {
    cat <<EOF >&2

Shut down and destroy Zimagi development environment (DESTRUCTIVE)

Usage:

  reactor destroy [flags] [options]

Flags:
${__zimagi_reactor_core_flags}

    --force               Force execution without confirming

EOF
  exit 1
}
function destroy_command () {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --force)
      FORCE=1
      ;;
      -h|--help)
      destroy_usage
      ;;
      *)
      if ! [ -z "$1" ]; then
        error "Unknown argument: ${1}"
        destroy_usage
      fi
      ;;
    esac
    shift
  done
  FORCE=${FORCE:-0}

  debug "Command: destroy"
  debug "> FORCE: ${FORCE}"

  if [ $FORCE -eq 0 ]; then
    confirm
  fi

  destroy_minikube
  remove_dns_records
  clean_terraform

  info "Zimagi development environment has been destroyed"
}
