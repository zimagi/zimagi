#
#=========================================================================================
# MiniKube Utilities
#

function push_minikube_image () {
  info "Pushing local Zimagi image to Minikube registry ..."
  if [ -f "${__zimagi_binary_dir}/minikube" ]; then
    "${__zimagi_binary_dir}"/minikube image load "$ZIMAGI_DEFAULT_RUNTIME_IMAGE"
  fi
}

function start_minikube () {
  info "Starting Minikube ..."
  if [ -f "${__zimagi_binary_dir}/minikube" ]; then
    "${__zimagi_binary_dir}"/minikube start \
      --driver=${MINIKUBE_DRIVER} \
      --nodes=${MINIKUBE_NODES} \
      --cpus=${MINIKUBE_CPUS} \
      --memory=${MINIKUBE_MEMORY} \
      --kubernetes-version=${MINIKUBE_KUBERNETES_VERSION} \
      --container-runtime=${MINIKUBE_CONTAINER_RUNTIME} \
      --addons="default-storageclass,storage-provisioner,metrics-server,dashboard"
  fi
}

function launch_minikube_tunnel () {
  info "Launching Minikube tunnel ..."
  if [ -f "${__zimagi_binary_dir}/minikube" ]; then
    "${__zimagi_binary_dir}"/minikube tunnel
  fi
}

function launch_minikube_dashboard () {
  info "Launching Kubernetes Dashboard ..."
  if [ -f "${__zimagi_binary_dir}/minikube" ]; then
    "${__zimagi_binary_dir}"/minikube dashboard &
  fi
}

function stop_minikube () {
  info "Stopping Minikube environment ..."
  if [ -f "${__zimagi_binary_dir}/minikube" ]; then
    if ! $("${__zimagi_binary_dir}"/minikube status > /dev/null); then
      "${__zimagi_binary_dir}"/minikube stop
    fi
  fi
}

function destroy_minikube () {
  info "Destroying Minikube environment ..."
  if [ -f "${__zimagi_binary_dir}/minikube" ]; then
    "${__zimagi_binary_dir}"/minikube delete --purge
  fi
}
