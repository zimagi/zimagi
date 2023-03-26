#
#=========================================================================================
# <Clean> Command
#

function clean_usage () {
    cat <<EOF >&2

Cleanup and wipe project resources (VERY DESTRUCTIVE)

Usage:

  reactor clean [flags] [options]

Flags:
${__zimagi_reactor_core_flags}

    --force               Force execution without confirming
    --all                 Clean everything
    --docker              Wipe all Docker resources

EOF
  exit 1
}
function clean_command () {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --force)
      FORCE=1
      ;;
      --all)
      CLEAN_ALL=1
      ;;
      --docker)
      WIPE_DOCKER=1
      ;;
      -h|--help)
      clean_usage
      ;;
      *)
      if ! [ -z "$1" ]; then
        error "Unknown argument: ${1}"
        clean_usage
      fi
      ;;
    esac
    shift
  done
  FORCE=${FORCE:-0}
  CLEAN_ALL=${CLEAN_ALL:-0}
  WIPE_DOCKER=${WIPE_DOCKER:-0}

  debug "Command: clean"
  debug "> FORCE: ${FORCE}"
  debug "> CLEAN_ALL: ${CLEAN_ALL}"
  debug "> WIPE_DOCKER: ${WIPE_DOCKER}"

  if [ $FORCE -eq 0 ]; then
    confirm
  fi

  destroy_minikube
  remove_dns_records

  if [[ $CLEAN_ALL -eq 1 ]] || [[ $WIPE_DOCKER -eq 1 ]]; then
    wipe_docker
  fi

  clean_terraform
  clean_certs

  info "Zimagi development environment has been cleaned"
}
