#
#=========================================================================================
# MiniKube Utilities
#

function minikube_status () {
  if [ -f "${__zimagi_binary_dir}/minikube" ]; then
    "${__zimagi_binary_dir}/minikube" status 1>/dev/null 2>&1
    return $?
  fi
  return 1
}

function push_minikube_image () {
  if minikube_status; then
    info "Pushing local Zimagi image to Minikube registry ..."
    "${__zimagi_binary_dir}/minikube" image load "$ZIMAGI_DEFAULT_RUNTIME_IMAGE"
  fi
}

function start_minikube () {
  if ! minikube_status; then
    info "Starting Minikube ..."
    "${__zimagi_binary_dir}/minikube" start \
      --driver=${MINIKUBE_DRIVER} \
      --nodes=${MINIKUBE_NODES} \
      --cpus=${MINIKUBE_CPUS} \
      --memory=${MINIKUBE_MEMORY} \
      --kubernetes-version=${MINIKUBE_KUBERNETES_VERSION} \
      --container-runtime=${MINIKUBE_CONTAINER_RUNTIME} \
      --addons="default-storageclass,storage-provisioner,metrics-server,dashboard" \
      --mount \
      --mount-string="${__zimagi_dir}:/project"
  fi
}

function launch_minikube_tunnel () {
  if minikube_status; then
    PID_FILE="${__zimagi_data_dir}/tunnel.kpid"
    LOG_FILE="${__zimagi_data_dir}/tunnel.log"

    terminate_minikube_tunnel

    info "Launching Minikube tunnel ..."
    "${__zimagi_binary_dir}/minikube" tunnel >"$LOG_FILE" 2>&1 &
    echo "$!" >"$PID_FILE"
  fi
}

function terminate_minikube_tunnel () {
  if minikube_status; then
    PID_FILE="${__zimagi_data_dir}/tunnel.kpid"
    LOG_FILE="${__zimagi_data_dir}/tunnel.log"

    info "Terminating existing Minikube tunnel ..."

    if [ -f "$PID_FILE" ]; then
      if kill -s 0 "$(cat "$PID_FILE")" >/dev/null 2>&1; then
        kill "$(cat "$PID_FILE")"
      fi
      rm -f "$PID_FILE"
    fi
    if [ -f "$LOG_FILE" ]; then
      rm -f "$LOG_FILE"
    fi
  fi
}

function launch_minikube_dashboard () {
  if minikube_status; then
    PID_FILE="${__zimagi_data_dir}/dashboard.kpid"
    LOG_FILE="${__zimagi_data_dir}/dashboard.log"

    terminate_minikube_dashboard

    info "Launching Kubernetes Dashboard ..."
    "${__zimagi_binary_dir}/minikube" dashboard >"$LOG_FILE" 2>&1 &
    echo "$!" >"$PID_FILE"
  fi
}

function terminate_minikube_dashboard () {
  if minikube_status; then
    PID_FILE="${__zimagi_data_dir}/dashboard.kpid"
    LOG_FILE="${__zimagi_data_dir}/dashboard.log"

    info "Terminating Minikube dashboard ..."

    if [ -f "$PID_FILE" ]; then
      if kill -s 0 "$(cat "$PID_FILE")" >/dev/null 2>&1; then
        kill "$(cat "$PID_FILE")"
      fi
      rm -f "$PID_FILE"
    fi
    if [ -f "$LOG_FILE" ]; then
      rm -f "$LOG_FILE"
    fi
  fi
}

function start_zimagi_session () {
  ZIMAGI_SERVICE="${1:-}"

  if ! minikube_status; then
    emergency "Minikube is not running"
  fi

  PODS=($("${__zimagi_binary_dir}/kubectl" get pods -n zimagi -l "app.kubernetes.io/name=zimagi" -o=jsonpath='{.items[*].metadata.name}' ))

  if ! [ ${#PODS[@]} -eq 0 ]; then
    if [ -z "$ZIMAGI_SERVICE" ]; then
      for index in $(seq 1 ${#PODS[@]}); do
        echo "[ ${index} ] - ${PODS[$index - 1]}"
      done
      read -p "Enter number: " POD_INPUT
      ZIMAGI_SERVICE="${PODS[$POD_INPUT-1]}"
    fi
    "${__zimagi_binary_dir}"/kubectl exec -n zimagi -ti "$ZIMAGI_SERVICE" -- bash
  else
    alert "Zimagi services are not running"
  fi
}

function stop_minikube () {
  info "Stopping Minikube environment ..."
  if minikube_status; then
    terminate_minikube_tunnel
    terminate_minikube_dashboard

    "${__zimagi_binary_dir}/minikube" stop
  fi
  delete_minikube_kubeconfig
}

function destroy_minikube () {
  info "Destroying Minikube environment ..."
  if [ -f "${__zimagi_binary_dir}/minikube" ]; then
    terminate_minikube_tunnel
    terminate_minikube_dashboard

    "${__zimagi_binary_dir}/minikube" delete --purge
  fi
  delete_minikube_kubeconfig
  delete_minikube_storage
  clean_helm
  clean_argocd
}

function delete_minikube_kubeconfig () {
  if [ -f "${__zimagi_binary_dir}/minikube" ]; then
    if [ -f "${__zimagi_data_dir}/.kubeconfig" ]; then
      info "Deleting Minikube kubeconfig file ..."
      rm -f "${__zimagi_data_dir}/.kubeconfig"
    fi
  fi
}

function delete_minikube_storage () {
  if [ -f "${__zimagi_binary_dir}/minikube" ]; then
    if [ -d "${__zimagi_data_dir}/minikube" ]; then
      info "Deleting Minikube project storage ..."
      sudo rm -Rf "${__zimagi_data_dir}/minikube"
    fi
  fi
}
