#
#=========================================================================================
# Terraform Utilities
#

function provision_terraform () {
  build_environment

  TERRAFORM_ARGS=(
    "--rm"
    "--network" "host"
    "--volume" "${KUBECONFIG}:/root/.kube/config"
    "--volume" "${__zimagi_cluster_dir}:/project"
    "--volume" "${HOME}/.minikube:${HOME}/.minikube"
    "--workdir" "/project"
    "hashicorp/terraform:1.4.2"
  )

  info "Generating Terraform configuration ..."
  cat > "${__zimagi_cluster_dir}/terraform.tfvars" <<EOF
#
# System variables
#
domain      = "${ZIMAGI_APP_NAME}.local"
environment = "Development"

#
# Repository Management variables
#
github_org            = "$ZIMAGI_GITHUB_ORG"
github_deployer_token = "$ZIMAGI_GITHUB_TOKEN"

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
zimagi_os_password         = "$ZIMAGI_USER_PASSWORD"
zimagi_admin_api_key       = "$ZIMAGI_ADMIN_API_KEY"
zimagi_email_host_user     = "${ZIMAGI_EMAIL_HOST_USER:-""}"
zimagi_email_host_password = "${ZIMAGI_EMAIL_HOST_PASSWORD:-""}"
EOF

  info "Initializing Terraform project ..."
  docker run "${TERRAFORM_ARGS[@]}" init

  info "Validating Terraform project ..."
  docker run "${TERRAFORM_ARGS[@]}" validate

  info "Deploying Zimagi cluster ..."
  docker run "${TERRAFORM_ARGS[@]}" apply -auto-approve -input=false
}

function clean_terraform () {
  info "Removing Terraform configuration ..."
  if [ -d "${__zimagi_cluster_dir}/.terraform" ]; then
    sudo rm -Rf "${__zimagi_cluster_dir}/.terraform"
    rm -f "${__zimagi_cluster_dir}/.terraform.lock.hcl"
    rm -f "${__zimagi_cluster_dir}/terraform.tfvars"
    rm -f "${__zimagi_cluster_dir}/terraform.tfstate"*
  fi
}
