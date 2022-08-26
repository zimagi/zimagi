#
#=========================================================================================
# Skaffold Utilities
#

function start_skaffold () {
  info "Starting Skaffold ..."

  if [ -f "${__zimagi_binary_dir}/minikube" -a -f "${__zimagi_binary_dir}/skaffold" ]; then
    info "Exporting Minikube Docker environment ..."
    eval $("${__zimagi_binary_dir}"/minikube docker-env)

    info "Generating certificate environment ..."
    build_environment

    info "Generating Helm values environment overrides ..."
    "${__zimagi_script_dir}/utilities/values.py" "${__zimagi_helm_values_file}"

    debug "Helm values overrides"
    debug "$(cat ${__zimagi_helm_values_file})"

    info "Generating Skaffold configuration from template ..."
    cat "${__zimagi_dir}/config/_skaffold.yml" | envsubst > "${__zimagi_dir}/skaffold.yaml"

    debug "Skaffold configuration"
    debug "$(cat ${__zimagi_dir}/skaffold.yaml)"

    info "Starting Skaffold ..."
    find "${__zimagi_app_dir}" -name *.pyc -exec rm -f {} \;
    find "${__zimagi_package_dir}" -name *.pyc -exec rm -f {} \;
    find "${__zimagi_lib_dir}" -name *.pyc -exec rm -f {} \;

    "${__zimagi_binary_dir}"/skaffold dev --port-forward
  fi
}
