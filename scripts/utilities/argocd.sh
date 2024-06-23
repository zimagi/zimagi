#
#=========================================================================================
# ArgoCD Utilities
#

function login_argocd () {
  if minikube_status; then
    info "Logging into ArgoCD via CLI ..."
    "${__zimagi_binary_dir}/argocd" login \
      "argocd.$(echo "$ZIMAGI_APP_NAME" | tr '_' '-').local" \
      --username admin --password \
      "${ARGOCD_ADMIN_PASSWORD:-admin}" \
      --insecure --grpc-web
  fi
}

function sync_zimagi_argocd_chart () {
  local chart_index_file="${__zimagi_argocd_charts_dir}/index.txt"

  generate_helm_template

  if minikube_status; then
    info "Syncing Zimagi chart into ArgoCD ..."

    login_argocd

    if "${__zimagi_binary_dir}/argocd" app get zimagi 2>&1 >/dev/null; then
      "${__zimagi_binary_dir}/argocd" app set zimagi --grpc-web --sync-policy none
      "${__zimagi_binary_dir}/argocd" app sync zimagi --prune --grpc-web \
        --local "${__zimagi_charts_dir}/charts/zimagi" >"${__zimagi_data_dir}/zimagi.sync.log" 2>&1

      if [ $? -ne 0 ]; then
        cat "${__zimagi_data_dir}/zimagi.sync.log"
      fi
    fi

    if [ -f "${chart_index_file}" ]; then
      while read -r LINE; do
        spec=(${LINE//=/})
        app_name="${spec[0]}"
        chart_path="${__zimagi_argocd_charts_dir}/${spec[1]}"

        if "${__zimagi_binary_dir}/argocd" app get "${app_name}" 2>&1 >/dev/null; then
          "${__zimagi_binary_dir}/argocd" app set "${app_name}" --grpc-web --sync-policy none
          "${__zimagi_binary_dir}/argocd" app sync "${app_name}" --prune --grpc-web \
            --local "$chart_path" >"${__zimagi_data_dir}/${app_name}.sync.log" 2>&1

          if [ $? -ne 0 ]; then
            cat "${__zimagi_data_dir}/${app_name}.sync.log"
          fi
        fi
      done < "${chart_index_file}"
    fi

    #for path in "${__zimagi_argocd_charts_dir}/"*/; do
    #  if [ -d "$path" ]; then
    #    echo $path
    #  fi
    #done
  fi
}

function clean_argocd () {
  info "Cleaning ArgoCD files ..."
  rm -f "${__zimagi_data_dir}/zimagi.sync.log"
}
