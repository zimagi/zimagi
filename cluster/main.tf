module "kubernetes_apps" {
  source = "github.com/zimagi/argocd-apps?ref=2.0.24"

  domain      = var.domain
  environment = var.environment

  argocd_config_path = "${path.module}/argocd"
  project_path       = "${path.module}/projects"

  project_sequence = [
    "system",
    "platform"
  ]

  variables = local.variables
}
