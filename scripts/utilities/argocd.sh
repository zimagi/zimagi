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
  generate_helm_template

  if minikube_status; then
    info "Syncing Zimagi chart into ArgoCD ..."

    login_argocd
    "${__zimagi_binary_dir}/argocd" app set zimagi --grpc-web --sync-policy none
    "${__zimagi_binary_dir}/argocd" app sync zimagi --prune --grpc-web \
      --local "${__zimagi_charts_dir}/charts/zimagi" >"${__zimagi_data_dir}/zimagi.sync.log" 2>&1

    if [ $? -ne 0 ]; then
      cat "${__zimagi_data_dir}/zimagi.sync.log"
    fi
  fi
}

function clean_argocd () {
  info "Cleaning ArgoCD files ..."
  rm -f "${__zimagi_data_dir}/zimagi.sync.log"
}
