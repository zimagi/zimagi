module "kubernetes_apps" {
  source = "./argocd-apps"

  domain      = var.domain
  environment = var.environment

  argocd_config_path = "${path.module}/argocd"
  project_path       = "${path.module}/projects"
  config_path        = "${path.module}/config"

  project_sequence = [
    "system",
    "platform",
    "database",
    "management"
  ]

  variables = local.variables
}
