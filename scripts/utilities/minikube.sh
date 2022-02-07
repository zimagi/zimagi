#
#=========================================================================================
# MiniKube Utilities
#


function install_shared_storage_server() {
  "${__zimagi_binary_dir}"/helm repo add nfs-ganesha-server-and-external-provisioner https://kubernetes-sigs.github.io/nfs-ganesha-server-and-external-provisioner/
  "${__zimagi_binary_dir}"/helm upgrade --install \
    nfs-server-provisioner \
    nfs-ganesha-server-and-external-provisioner/nfs-server-provisioner
}

function start_minikube () {
  info "Starting Minikube ..."
  "${__zimagi_binary_dir}"/minikube start \
    --driver=${MINIKUBE_DRIVER:-docker} \
    --cpus=${MINIKUBE_CPUS} \
    --kubernetes-version=${MINIKUBE_KUBERNETES_VERSION} \
    --container-runtime=${MINIKUBE_CONTAINER_RUNTIME}
  info "Installing Shared Storage Server ..."
  install_shared_storage_server
}

function stop_minikube () {
  info "Stopping Minikube environment ..."
  if ! $("${__zimagi_binary_dir}"/minikube status > /dev/null); then
    "${__zimagi_binary_dir}"/minikube stop
  fi
}

function destroy_minikube () {
  info "Destroying Minikube environment ..."
  "${__zimagi_binary_dir}"/minikube delete --purge
}

function zimagi_status () {
  if ! $("${__zimagi_binary_dir}"/minikube status > /dev/null); then
    emergency "Minikube is not running"
  fi
  echo
  "${__zimagi_binary_dir}"/minikube status
  "${__zimagi_binary_dir}"/kubectl get pods -l "app.kubernetes.io/name=zimagi"
  echo
}

function start_zimagi_session () {
  ZIMAGI_SERVICE="$1"

  if ! $("${__zimagi_binary_dir}"/minikube status > /dev/null); then
    emergency "Minikube is not running"
  fi
  PODS=($("${__zimagi_binary_dir}"/kubectl get pods -l "app.kubernetes.io/name=zimagi" -o=jsonpath='{.items[*].metadata.name}' ))
  if ! [ ${#PODS[@]} -eq 0 ]; then
    if [ -z "$ZIMAGI_SERVICE" ]; then
      for index in $(seq 1 ${#PODS[@]}); do
        echo "${index}.) ${PODS[$index - 1]}"
      done
      read -p "Enter number: " POD_INPUT
      ZIMAGI_SERVICE=${PODS[$POD_INPUT-1]}
    fi
    "${__zimagi_binary_dir}"/kubectl exec -ti $ZIMAGI_SERVICE -- bash
  else
    alert "Zimagi is not running"
  fi
}

function reload_zimagi () {
  SCHEDULER_POD=$("${__zimagi_binary_dir}"/kubectl get pods -l 'app.kubernetes.io/component=scheduler' -o=jsonpath='{.items[*].metadata.name}' )
  WORKER_POD=$("${__zimagi_binary_dir}"/kubectl get pods -l 'app.kubernetes.io/component=worker' -o=jsonpath='{.items[*].metadata.name}' )
  COMMAND_API_POD=$("${__zimagi_binary_dir}"/kubectl get pods -l 'app.kubernetes.io/component=command-api' -o=jsonpath='{.items[*].metadata.name}' )
  DATA_API_POD=$("${__zimagi_binary_dir}"/kubectl get pods -l 'app.kubernetes.io/component=data-api' -o=jsonpath='{.items[*].metadata.name}' )

  PODS=$(printf "%s %s %s %s" $SCHEDULER_POD $WORKER_POD $COMMAND_API_POD $DATA_API_POD)
  info "Reloading pods: ${PODS}"
  for pod in $PODS; do
    "${__zimagi_binary_dir}"/kubectl delete pod $pod &
  done
}
