#
#=========================================================================================
# Helm Utilities
#

function update_helm_dependencies () {
  if [ -f "${__zimagi_binary_dir}/helm" ]; then
    info "Updating Zimagi chart Helm dependencies ..."
    "${__zimagi_binary_dir}/helm" dependency update \
      "${__zimagi_charts_dir}/charts/zimagi"
  fi
}

function generate_helm_template () {
  if [ -f "${__zimagi_binary_dir}/helm" ]; then
    update_helm_dependencies

    TEMPLATE_ARGS=(
      "template"
      "zimagi"
      "${__zimagi_charts_dir}/charts/zimagi"
      "-f" "${__zimagi_cluster_dir}/projects/platform/zimagi/values.yaml"
      "-n" "zimagi"
    )

    info "Generating Zimagi Helm template ..."
    "${__zimagi_binary_dir}/helm" "${TEMPLATE_ARGS[@]}" >"${__zimagi_data_dir}/zimagi.helm.template.yml" 2>&1

    if [ $? -ne 0 ]; then
      "${__zimagi_binary_dir}/helm" "${TEMPLATE_ARGS[@]}" --debug
    fi
  fi
}

function clean_helm () {
  info "Cleaning Helm files ..."
  rm -f "${__zimagi_data_dir}/zimagi.helm.template.yml"
}
