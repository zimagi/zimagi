#
#=========================================================================================
# MiniKube Utilities
#

function start_minikube () {
  info "Starting Minikube ..."
  exit_code=$($__binary_dir/minikube start \
    --driver=${MINIKUBE_DRIVER:-docker} \
    --cpus=${MINIKUBE_CPUS:-2} \
    --kubernetes-version=${MINIKUBE_KUBERNETES_VERSION:-1.20.7} \
    --container-runtime=${MINIKUBE_CONTAINER_RUNTIME:-docker} \
  )
  debug "Exit code: ${exit_code}"
}

function stop_minikube () {
  info "Stopping Minikube environment ..."
  if ! $($__binary_dir/minikube status > /dev/null); then
    exit_code=$($__binary_dir/minikube stop)
    debug "Exit code: ${exit_code}"
  fi
}

function destroy_minikube () {
  info "Destroying Minikube environment ..."
  exit_code=$($__binary_dir/minikube delete --purge)
  debug "Exit code: ${exit_code}"
}

function get_zimagi_status () {
  if ! $($__binary_dir/minikube status > /dev/null); then
    emergency "Minikube is not running"
  fi
  echo
  $__binary_dir/minikube status
  $__binary_dir/kubectl get pods -l "app.kubernetes.io/name=zimagi"
  echo
}

function start_zimagi_session () {
  ZIMAGI_SERVICE="$1"

  if ! $($__binary_dir/minikube status > /dev/null); then
    emergency "Minikube is not running"
  fi
  PODS=($($__binary_dir/kubectl get pods -l "app.kubernetes.io/name=zimagi" -o=jsonpath='{.items[*].metadata.name}' ))
  if ! [ ${#PODS[@]} -eq 0 ]; then
    if [ -z "$ZIMAGI_SERVICE" ]; then
      for index in $(seq 1 ${#PODS[@]}); do
        echo "${index}.) ${PODS[$index - 1]}"
      done
      read -p "Enter number: " POD_INPUT
      ZIMAGI_SERVICE=${PODS[$POD_INPUT-1]}
    fi
    kubectl exec -ti $ZIMAGI_SERVICE bash
  else
    alert "Zimagi is not running"
  fi
}

function reload_zimagi () {
  SCHEDULER_POD=$($__binary_dir/kubectl get pods -l 'app.kubernetes.io/component=scheduler' -o=jsonpath='{.items[*].metadata.name}' )
  WORKER_POD=$($__binary_dir/kubectl get pods -l 'app.kubernetes.io/component=worker' -o=jsonpath='{.items[*].metadata.name}' )
  COMMAND_API_POD=$($__binary_dir/kubectl get pods -l 'app.kubernetes.io/component=command-api' -o=jsonpath='{.items[*].metadata.name}' )
  DATA_API_POD=$($__binary_dir/kubectl get pods -l 'app.kubernetes.io/component=data-api' -o=jsonpath='{.items[*].metadata.name}' )

  PODS=$(printf "%s %s %s %s" $SCHEDULER_POD $WORKER_POD $COMMAND_API_POD $DATA_API_POD)
  info "Reloading pods: ${PODS}"
  for pod in $PODS; do
    kubectl delete pod $pod &
  done
}
