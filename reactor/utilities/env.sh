#
#=========================================================================================
# Environment Generators
#

function docker_environment () {
  DOCKER_BASE_IMAGE="${ZIMAGI_BASE_IMAGE:-$DEFAULT_ZIMAGI_BASE_IMAGE}"
  DOCKER_RUNTIME="$1"
  DOCKER_TAG="$2"
  DOCKER_EXECUTABLE=docker
  DOCKER_FILE=Dockerfile

  debug "Setting Docker environment ..."
  debug "> DOCKER_BASE_IMAGE: ${DOCKER_BASE_IMAGE}"
  debug "> DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "> DOCKER_TAG: ${DOCKER_TAG}"

  if [ "$DOCKER_RUNTIME" == "standard" ]; then
    DOCKER_PARENT_IMAGE="$ZIMAGI_STANDARD_PARENT_IMAGE"
  else
    DOCKER_TAG="${DOCKER_RUNTIME}-${DOCKER_TAG}"

    if [ "$DOCKER_RUNTIME" == "nvidia" ]; then
      DOCKER_PARENT_IMAGE="$ZIMAGI_NVIDIA_PARENT_IMAGE"
    else
      emergency "Zimagi Docker runtime not supported: ${DOCKER_RUNTIME}"
    fi
  fi

  DOCKER_GROUP="$(stat -L -c '%g' /var/run/docker.sock)"

  export DOCKER_GROUP
  export DOCKER_RUNTIME
  export DOCKER_TAG
  export DOCKER_FILE="${__zimagi_docker_dir}/${DOCKER_FILE}"
  export DOCKER_PARENT_IMAGE
  export DOCKER_BASE_IMAGE
  export DOCKER_RUNTIME_IMAGE="${DOCKER_BASE_IMAGE}:${DOCKER_TAG}"

  debug "export DOCKER_GROUP: ${DOCKER_GROUP}"
  debug "export DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "export DOCKER_TAG: ${DOCKER_TAG}"
  debug "export DOCKER_FILE: ${DOCKER_FILE}"
  debug "export DOCKER_PARENT_IMAGE: ${DOCKER_PARENT_IMAGE}"
  debug "export DOCKER_BASE_IMAGE: ${DOCKER_RUNTIME_IMAGE}"
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
  export ZIMAGI_HOST_PACKAGE_DIR="${ZIMAGI_HOST_PACKAGE_DIR:-"${__zimagi_dir}/package"}"

  debug "export ZIMAGI_HOST_APP_DIR: ${ZIMAGI_HOST_APP_DIR}"
  debug "export ZIMAGI_HOST_DATA_DIR: ${ZIMAGI_HOST_DATA_DIR}"
  debug "export ZIMAGI_HOST_LIB_DIR: ${ZIMAGI_HOST_LIB_DIR}"
  debug "export ZIMAGI_HOST_PACKAGE_DIR: ${ZIMAGI_HOST_PACKAGE_DIR}"
}

function security_environment () {
  debug "Setting security environment ..."
  export ZIMAGI_USER_PASSWORD="${1:-$DEFAULT_USER_PASSWORD}"
  export ZIMAGI_DATA_KEY="${2:-$DEFAULT_DATA_KEY}"
  export ZIMAGI_ADMIN_API_KEY="${3:-$DEFAULT_ADMIN_API_KEY}"
  export ZIMAGI_ADMIN_API_TOKEN="${4:-$DEFAULT_ADMIN_API_TOKEN}"

  debug "export ZIMAGI_USER_PASSWORD: ${ZIMAGI_USER_PASSWORD}"
  debug "export ZIMAGI_DATA_KEY: ${ZIMAGI_DATA_KEY}"
  debug "export ZIMAGI_ADMIN_API_KEY: ${ZIMAGI_ADMIN_API_KEY}"
  debug "export ZIMAGI_ADMIN_API_TOKEN: ${ZIMAGI_ADMIN_API_TOKEN}"
}

function init_environment () {
  APP_NAME="$1"
  DOCKER_RUNTIME="$2"
  DOCKER_TAG="$3"
  USER_PASSWORD="$4"
  DATA_KEY="$5"
  ADMIN_API_KEY="$6"
  ADMIN_API_TOKEN="$7"

  debug "Initializing environment ..."
  debug "> APP_NAME: ${APP_NAME}"
  debug "> DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "> DOCKER_TAG: ${DOCKER_TAG}"
  debug "> USER_PASSWORD: ${USER_PASSWORD}"
  debug "> DATA_KEY: ${DATA_KEY}"
  debug "> ADMIN_API_KEY: ${ADMIN_API_KEY}"
  debug "> ADMIN_API_TOKEN: ${ADMIN_API_TOKEN}"

  docker_environment "$DOCKER_RUNTIME" "$DOCKER_TAG"
  security_environment "$USER_PASSWORD" "$DATA_KEY" "$ADMIN_API_KEY" "$ADMIN_API_TOKEN"

  info "Saving runtime configuration ..."
  cat > "${__zimagi_runtime_env_file}" <<EOF
# Minikube configurations
export KUBECONFIG="${__zimagi_data_dir}/.kubeconfig"

# Application configurations
export ZIMAGI_APP_NAME="${APP_NAME}"

export ZIMAGI_DOCKER_FILE="${DOCKER_FILE}"
export ZIMAGI_DOCKER_TAG="${DOCKER_TAG}"
export ZIMAGI_DOCKER_EXECUTABLE="${DOCKER_EXECUTABLE}"
export ZIMAGI_DOCKER_RUNTIME="${DOCKER_RUNTIME}"
export ZIMAGI_DOCKER_GROUP=${DOCKER_GROUP}

export ZIMAGI_PARENT_IMAGE="${DOCKER_PARENT_IMAGE}"
export ZIMAGI_BASE_IMAGE="${DOCKER_BASE_IMAGE}"
export ZIMAGI_DEFAULT_RUNTIME_IMAGE="${DOCKER_RUNTIME_IMAGE}"

export ZIMAGI_USER_UID=$(id -u)
export ZIMAGI_USER_PASSWORD="${ZIMAGI_USER_PASSWORD}"
export ZIMAGI_DATA_KEY="${ZIMAGI_DATA_KEY}"
export ZIMAGI_ADMIN_API_KEY="${ZIMAGI_ADMIN_API_KEY}"
export ZIMAGI_DEFAULT_ADMIN_TOKEN="${ZIMAGI_ADMIN_API_TOKEN}"
EOF
  debug ">> ${__zimagi_runtime_env_file}: $(cat ${__zimagi_runtime_env_file})"

  info "Importing new Zimagi environment configuration ..."
  import_environment
}

function import_environment () {
  if [ -f "${__zimagi_runtime_env_file}" ]; then
    source "${__zimagi_runtime_env_file}"
  fi
  host_environment

  debug "Environment variables"
  debug "======================================"
  debug "$(env)"
}
