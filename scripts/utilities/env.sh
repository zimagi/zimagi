#
#=========================================================================================
# Environment Generators
#

function docker_environment () {
  DOCKER_BASE_IMAGE="${ZIMAGI_BASE_IMAGE:-zimagi/zimagi}"
  DOCKER_RUNTIME="$1"
  DOCKER_TAG="$2"
  DOCKER_EXECUTABLE=docker

  debug "Function: docker_environment"
  debug "> DOCKER_BASE_IMAGE: ${DOCKER_BASE_IMAGE}"
  debug "> DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "> DOCKER_TAG: ${DOCKER_TAG}"

  if [ "$DOCKER_RUNTIME" = "standard" ]; then
    DOCKER_FILE=Dockerfile
    DOCKER_TAG=$DOCKER_TAG
    DOCKER_RUNTIME=standard
  else
    DOCKER_FILE="Dockerfile.${DOCKER_RUNTIME}"
    DOCKER_TAG="${DOCKER_RUNTIME}-${DOCKER_TAG}"

    if which nvidia-docker >/dev/null 2>&1 && [ "$DOCKER_RUNTIME" == "nvidia" ]; then
      DOCKER_EXECUTABLE=nvidia-docker
      DOCKER_RUNTIME=nvidia
    else
      DOCKER_RUNTIME=standard
    fi
  fi

  export DOCKER_EXECUTABLE
  export DOCKER_RUNTIME
  export DOCKER_TAG
  export DOCKER_FILE="${__zimagi_docker_dir}/${DOCKER_FILE}"
  export DOCKER_BASE_IMAGE
  export DOCKER_RUNTIME_IMAGE="${DOCKER_BASE_IMAGE}:${DOCKER_TAG}"

  debug "export DOCKER_EXECUTABLE: ${DOCKER_EXECUTABLE}"
  debug "export DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "export DOCKER_TAG: ${DOCKER_TAG}"
  debug "export DOCKER_FILE: ${DOCKER_FILE}"
  debug "export DOCKER_RUNTIME_IMAGE: ${DOCKER_RUNTIME_IMAGE}"
}

function build_environment () {
  debug "Setting certificate environment ..."
  export ZIMAGI_CA_KEY="$(cat "${__zimagi_certs_dir}/zimagi-ca.key")"
  export ZIMAGI_CA_CERT="$(cat "${__zimagi_certs_dir}/zimagi-ca.crt")"
  export ZIMAGI_KEY="$(cat "${__zimagi_certs_dir}/zimagi.key")"
  export ZIMAGI_CERT="$(cat "${__zimagi_certs_dir}/zimagi.crt")"

  debug "export ZIMAGI_CA_KEY: ${ZIMAGI_CA_KEY}"
  debug "export ZIMAGI_CA_CERT: ${ZIMAGI_CA_CERT}"
  debug "export ZIMAGI_KEY: ${ZIMAGI_KEY}"
  debug "export ZIMAGI_CERT: ${ZIMAGI_CERT}"
}

function host_environment () {
  debug "Setting host environment ..."
  export ZIMAGI_HOST_APP_DIR="${ZIMAGI_HOST_APP_DIR:-"${__zimagi_dir}/app"}"
  export ZIMAGI_HOST_DATA_DIR="${ZIMAGI_HOST_DATA_DIR:-"${__zimagi_dir}/data"}"
  export ZIMAGI_HOST_LIB_DIR="${ZIMAGI_HOST_LIB_DIR:-"${__zimagi_dir}/lib"}"
  export ZIMAGI_HOST_COMMAND_PORT=${ZIMAGI_HOST_COMMAND_PORT:-5123}
  export ZIMAGI_HOST_DATA_PORT=${ZIMAGI_HOST_DATA_PORT:-5323}

  debug "export ZIMAGI_HOST_APP_DIR: ${ZIMAGI_HOST_APP_DIR}"
  debug "export ZIMAGI_HOST_DATA_DIR: ${ZIMAGI_HOST_DATA_DIR}"
  debug "export ZIMAGI_HOST_LIB_DIR: ${ZIMAGI_HOST_LIB_DIR}"
  debug "export ZIMAGI_HOST_COMMAND_PORT: ${ZIMAGI_HOST_COMMAND_PORT}"
  debug "export ZIMAGI_HOST_DATA_PORT: ${ZIMAGI_HOST_DATA_PORT}"
}

function security_environment () {
  ZIMAGI_DATA_KEY="$1"

  debug "Function: security_environment"
  debug "> ZIMAGI_DATA_KEY: ${ZIMAGI_DATA_KEY}"

  if [ -z "$ZIMAGI_DATA_KEY" ]; then
    ZIMAGI_DATA_KEY="$DEFAULT_DATA_KEY"
  fi
  export ZIMAGI_DATA_KEY

  debug "export ZIMAGI_DATA_KEY: ${ZIMAGI_DATA_KEY}"
}

function init_environment () {
  APP_NAME="$1"
  DOCKER_RUNTIME="$2"
  DOCKER_TAG="$3"
  DATA_KEY="$4"

  debug "Function: init_environment"
  debug "> APP_NAME: ${APP_NAME}"
  debug "> DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "> DOCKER_TAG: ${DOCKER_TAG}"
  debug "> DATA_KEY: ${DATA_KEY}"

  docker_environment "$DOCKER_RUNTIME" "$DOCKER_TAG"
  security_environment "$DATA_KEY"

  info "Saving runtime configuration ..."
  cat > "${__zimagi_runtime_env_file}" <<EOF
# Application configurations
export ZIMAGI_APP_NAME="${APP_NAME}"

export ZIMAGI_DOCKER_FILE="${DOCKER_FILE}"
export ZIMAGI_DOCKER_TAG="${DOCKER_TAG}"
export ZIMAGI_DOCKER_EXECUTABLE="${DOCKER_EXECUTABLE}"
export ZIMAGI_DOCKER_RUNTIME="${DOCKER_RUNTIME}"
export ZIMAGI_BASE_IMAGE="${DOCKER_BASE_IMAGE}"
export ZIMAGI_DEFAULT_RUNTIME_IMAGE="${DOCKER_RUNTIME_IMAGE}"

# Docker image build arguments
export ZIMAGI_DATA_KEY="${ZIMAGI_DATA_KEY}"

# Minikube configurations
export MINIKUBE_CPUS=${MINIKUBE_CPUS:-2}
export MINIKUBE_KUBERNETES_VERSION="${MINIKUBE_KUBERNETES_VERSION:-1.23.1}"
export MINIKUBE_CONTAINER_RUNTIME="${MINIKUBE_CONTAINER_RUNTIME:-docker}"
export MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-skaffold}"

# Helm configurations
export HELM_VERSION="${HELM_VERSION:-3.8.0}"
EOF
  debug ">> ${__zimagi_runtime_env_file}: $(cat ${__zimagi_runtime_env_file})"

  info "Initializing Zimagi environment configuration ..."
  if ! [ -f "${__zimagi_app_env_file}" ]; then
    cat > "${__zimagi_app_env_file}" <<EOF
# Application configurations
export ZIMAGI_SECRET_KEY="${ZIMAGI_SECRET_KEY:-XXXXXX20181105}"
export ZIMAGI_POSTGRES_DB="${ZIMAGI_POSTGRES_DB:-zimagi}"
export ZIMAGI_POSTGRES_USER="${ZIMAGI_POSTGRES_USER:-zimagi}"
export ZIMAGI_POSTGRES_PASSWORD="${ZIMAGI_POSTGRES_PASSWORD:-A1B3C5D7E9F10}"
export ZIMAGI_REDIS_PASSWORD="${ZIMAGI_REDIS_PASSWORD:-A1B3C5D7E9F10}"

# Dynamic configuration overrides
EOF
    ignore_vars=(
        "ZIMAGI_APP_NAME"
        "ZIMAGI_DOCKER_FILE"
        "ZIMAGI_DOCKER_TAG"
        "ZIMAGI_DOCKER_RUNTIME"
        "ZIMAGI_DEFAULT_RUNTIME_IMAGE"
        "ZIMAGI_CA_KEY"
        "ZIMAGI_CA_CERT"
        "ZIMAGI_KEY"
        "ZIMAGI_CERT"
        "ZIMAGI_DATA_KEY"
        "MINIKUBE_CPUS"
        "MINIKUBE_KUBERNETES_VERSION"
        "MINIKUBE_CONTAINER_RUNTIME"
        "MINIKUBE_PROFILE"
        "ZIMAGI_HOST_APP_DIR"
        "ZIMAGI_HOST_DATA_DIR"
        "ZIMAGI_HOST_LIB_DIR"
        "ZIMAGI_HOST_COMMAND_PORT"
        "ZIMAGI_HOST_DATA_PORT"
        "ZIMAGI_SECRET_KEY"
        "ZIMAGI_POSTGRES_DB"
        "ZIMAGI_POSTGRES_USER"
        "ZIMAGI_POSTGRES_PASSWORD"
        "ZIMAGI_REDIS_PASSWORD"
    )
    while IFS= read -r variable; do
      if [[ ! " ${ignore_vars[*]} " =~ " ${variable} " ]]; then
        echo "export ${variable}=\"$(printenv $variable)\"" >> "${__zimagi_app_env_file}"
      fi
    done <<< "$(env | grep -Po "ZIMAGI_[_A-Z0-9]+")"
    info "Zimagi environment configuration saved"
  fi
  debug ">> ${__zimagi_app_env_file}: $(cat "${__zimagi_app_env_file}")"

  info "Importing new Zimagi environment configuration ..."
  import_environment
}

function import_environment () {
  if [ -f "${__zimagi_app_env_file}" ]; then
    source "${__zimagi_app_env_file}"
  fi
  if [ -f "${__zimagi_runtime_env_file}" ]; then
    source "${__zimagi_runtime_env_file}"
  fi
  host_environment
}
