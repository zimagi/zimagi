#
#=========================================================================================
# Skaffold Utilities
#

function start_skaffold () {
  info "Starting Skaffold ..."

  eval $($__binary_dir/minikube docker-env)

  info "Generating Skaffold configuration from template ..."
  cat "$__dir/_skaffold.yaml" | envsubst > "$__dir/skaffold.yaml"

  debug "Skaffold configuration"
  debug "$(cat $__dir/skaffold.yaml)"

  info "Starting Skaffold ..."
  exit_code=$($__binary_dir/skaffold dev --port-forward)
  debug "Exit code: ${exit_code}"
}
