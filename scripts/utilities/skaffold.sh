#
#=========================================================================================
# Skaffold Utilities
#

function start_skaffold () {
  info "Starting Skaffold ..."

  info "Exporting Minikube Docker environment ..."
  eval $("${__zimagi_binary_dir}"/minikube docker-env)

  info "Generating certificate environment ..."
  build_environment

  info "Generating Skaffold configuration from template ..."
  cat "${__zimagi_dir}/config/_skaffold.yml" | envsubst > "${__zimagi_dir}/skaffold.yaml"

  debug "Skaffold configuration"
  debug "$(cat ${__zimagi_dir}/skaffold.yaml)"

  info "Starting Skaffold ..."
  "${__zimagi_binary_dir}"/skaffold dev --port-forward
}
