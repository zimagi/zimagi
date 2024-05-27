#
#=========================================================================================
# Terraform Utilities
#

function provision_terraform () {
  if minikube_status; then
    build_environment

    TERRAFORM_ARGS=(
      "--rm"
      "--network" "host"
      "--volume" "${KUBECONFIG}:/root/.kube/config"
      "--volume" "${__zimagi_cluster_dir}:/project"
      "--volume" "${HOME}/.minikube:${HOME}/.minikube"
      "--workdir" "/project"
      "hashicorp/terraform:1.8.4"
    )

    TERRAFORM_VARS="${__zimagi_cluster_dir}/terraform.tfvars"
    TERRAFORM_CUSTOM_VARS="${__zimagi_cluster_dir}/terraform.custom.tfvars"

    info "Generating Terraform configuration ..."
    cat > "$TERRAFORM_VARS" <<EOF
#
# System variables
#
domain      = "$(echo "$ZIMAGI_APP_NAME" | tr '_' '-').local"
environment = "Development"

#
# Repository Management variables
#
github_org            = "${ZIMAGI_GITHUB_ORG:-}"
github_deployer_token = "${ZIMAGI_GITHUB_TOKEN:-}"

#
# Networking variables
#
gateway_node_port = 32210
ssl_certificate = <<-EOT
$ZIMAGI_CERT
EOT
ssl_private_key = <<-EOT
$ZIMAGI_KEY
EOT

#
# ArgoCD variables
#
argocd_admin_password = "$("${__zimagi_binary_dir}/argocd" account bcrypt --password "${ARGOCD_ADMIN_PASSWORD:-admin}")"

#
# Zimagi variables
#
zimagi_tag                 = "$ZIMAGI_DOCKER_TAG"
zimagi_os_password         = "$ZIMAGI_USER_PASSWORD"
zimagi_admin_api_key       = "$ZIMAGI_ADMIN_API_KEY"
zimagi_email_host_user     = "${ZIMAGI_EMAIL_HOST_USER:-}"
zimagi_email_host_password = "${ZIMAGI_EMAIL_HOST_PASSWORD:-}"
EOF
    if [ -f "$TERRAFORM_CUSTOM_VARS" ]; then
      echo "$(cat "$TERRAFORM_CUSTOM_VARS")" >> "$TERRAFORM_VARS"
    fi

    info "Initializing Terraform project ..."
    docker run "${TERRAFORM_ARGS[@]}" init

    info "Validating Terraform project ..."
    docker run "${TERRAFORM_ARGS[@]}" validate

    info "Deploying Zimagi cluster ..."
    docker run "${TERRAFORM_ARGS[@]}" apply -auto-approve -input=false
  fi
}

function clean_terraform () {
  if [ -d "${__zimagi_cluster_dir}/.terraform" ]; then
    info "Removing Terraform configuration ..."
    sudo rm -Rf "${__zimagi_cluster_dir}/.terraform"
    rm -f "${__zimagi_cluster_dir}/.terraform.lock.hcl"
    rm -f "${__zimagi_cluster_dir}/terraform.tfvars"
    rm -f "${__zimagi_cluster_dir}/terraform.tfstate"*
  fi
}
