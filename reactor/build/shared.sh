
function init_certs() {
  cert_environment

  export ZIMAGI_CA_KEY="${APP_CA_KEY:-}"
  export ZIMAGI_CA_CERT="${APP_CA_CERT:-}"
  export ZIMAGI_KEY="${APP_KEY:-}"
  export ZIMAGI_CERT="${APP_CERT:-}"
}

function server_build_args() {
  init_certs
  zimagi_environment

  export DOCKER_BUILD_VARS=(
    "ZIMAGI_PARENT_IMAGE"
    "ZIMAGI_ENVIRONMENT=${__environment}"
    "ZIMAGI_USER_UID=$(id -u)"
    "ZIMAGI_USER_PASSWORD"
    "ZIMAGI_CA_KEY"
    "ZIMAGI_CA_CERT"
    "ZIMAGI_KEY"
    "ZIMAGI_CERT"
    "ZIMAGI_DATA_KEY"
    "ZIMAGI_DEFAULT_MODULES"
  )
}

function client_build_args() {
  zimagi_environment

  export DOCKER_BUILD_VARS=(
    "ZIMAGI_PARENT_IMAGE"
    "ZIMAGI_ENVIRONMENT=${__environment}"
    "ZIMAGI_USER_UID=$(id -u)"
  )
}
