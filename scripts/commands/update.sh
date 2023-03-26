#
#=========================================================================================
# <Update> Command
#

function update_usage () {
    cat <<EOF >&2

Update the application stack in the Minikube environment.

Usage:

  reactor update [flags] [options]

Flags:
${__zimagi_reactor_core_flags}

    --image               Push local Zimagi image to Minikube registry
    --apps                Provision any ArgoCD application updates
    --dns                 Update local DNS with service endpoints
    --chart               Sync local Zimagi chart to ArgoCD application

EOF
  exit 1
}
function update_command () {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --image)
      UPDATE_IMAGE=1
      ;;
      --apps)
      UPDATE_APPS=1
      ;;
      --dns)
      UPDATE_DNS=1
      ;;
      --chart)
      UPDATE_CHART=1
      ;;
      -h|--help)
      update_usage
      ;;
      *)
      if ! [ -z "$1" ]; then
        error "Unknown argument: ${1}"
        update_usage
      fi
      ;;
    esac
    shift
  done
  UPDATE_IMAGE=${UPDATE_IMAGE:-0}
  UPDATE_APPS=${UPDATE_APPS:-0}
  UPDATE_DNS=${UPDATE_DNS:-0}
  UPDATE_CHART=${UPDATE_CHART:-0}
  UPDATE_ALL=1

  if [ $UPDATE_IMAGE -eq 1 -o $UPDATE_APPS -eq 1 -o $UPDATE_DNS -eq 1 -o $UPDATE_CHART -eq 1 ]; then
    UPDATE_ALL=0
  fi

  debug "Command: update"
  debug "> UPDATE_IMAGE: ${UPDATE_IMAGE}"
  debug "> UPDATE_APPS: ${UPDATE_APPS}"
  debug "> UPDATE_DNS: ${UPDATE_DNS}"
  debug "> UPDATE_CHART: ${UPDATE_CHART}"
  debug "> UPDATE_ALL: ${UPDATE_ALL}"

  if [ $UPDATE_ALL -eq 1 -o $UPDATE_IMAGE -eq 1 ]; then
    push_minikube_image
  fi
  if [ $UPDATE_ALL -eq 1 -o $UPDATE_IMAGE -eq 1 -o $UPDATE_APPS -eq 1 ]; then
    provision_terraform
  fi
  if [ $UPDATE_ALL -eq 1 -o $UPDATE_DNS -eq 1 ]; then
    save_dns_records
  fi
  if [ $UPDATE_ALL -eq 1 -o $UPDATE_IMAGE -eq 1 -o $UPDATE_CHART -eq 1 ]; then
    sync_zimagi_argocd_chart
  fi
  info "Zimagi development environment has been updated"
}
