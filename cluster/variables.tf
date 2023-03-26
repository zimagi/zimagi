#
# System variables
#
variable "domain" {
  description = "Platform domain"
  type        = string
}
variable "environment" {
  description = "Platform Environment"
  type        = string
  default     = "Development"
}

#
# Filesystem variables
#
variable "kube_config" {
  description = "Kubernetes cluster credential file (~/.kube/config)."
  type        = string
  default     = "~/.kube/config"
}

#
# Repository Management variables
#
variable "github_org" {
  description = "GitHub organization"
  type        = string
  default     = ""
}
variable "github_deployer_token" {
  description = "GitHub organization deployer account token (can access repositories and create deploy keys)"
  type        = string
  default     = ""
}

#
# Networking variables
#
variable "gateway_node_port" {
  description = "Kubernetes Gateway Ingress Node port"
  type        = number
  default     = 32210
}

variable "ssl_certificate" {
  description = "The certificate for the origin server SSL termination"
  type        = string
}
variable "ssl_private_key" {
  description = "The certificate private key for the origin server SSL termination"
  type        = string
}

#
# ArgoCD variables
#
variable "argocd_admin_password" {
  description = "ArgoCD administrator password (bcrypt hash)"
  type        = string
}

#
# Zimagi variables
#
variable "zimagi_tag" {
  description = "Zimagi Container Image Tag"
  type        = string
  default     = "dev"
}
variable "zimagi_os_password" {
  description = "Zimagi OS user password"
  type        = string
}

variable "zimagi_admin_api_key" {
  description = "Zimagi API Administrator Encryption Key"
  type        = string
}

variable "zimagi_email_host_user" {
  description = "Zimagi Email Host User"
  type        = string
  default     = ""
}
variable "zimagi_email_host_password" {
  description = "Zimagi Email Host Password"
  type        = string
  default     = ""
}
