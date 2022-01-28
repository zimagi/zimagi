#
#=========================================================================================
# Environment Generators
#

function docker_environment () {
  DOCKER_BASE_IMAGE="${ZIMAGI_BASE_IMAGE:-zimagi/zimagi}"
  DOCKER_RUNTIME="$1"
  DOCKER_TAG="$2"

  debug "Function: docker_environment"
  debug "> DOCKER_BASE_IMAGE: ${DOCKER_BASE_IMAGE}"
  debug "> DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "> DOCKER_TAG: ${DOCKER_TAG}"

  info "Setting Docker environment"
  if [ "$DOCKER_RUNTIME" = "standard" ]; then
    DOCKER_FILE=Dockerfile
    DOCKER_TAG=$DOCKER_TAG
    DOCKER_RUNTIME=standard
  else
    DOCKER_FILE="Dockerfile.${DOCKER_RUNTIME}"
    DOCKER_TAG="${DOCKER_RUNTIME}-${DOCKER_TAG}"

    if which nvidia-docker >/dev/null 2>&1 && [ "$DOCKER_RUNTIME" == "nvidia" ]; then
      DOCKER_RUNTIME=nvidia
    else
      DOCKER_RUNTIME=standard
    fi
  fi
  export DOCKER_RUNTIME
  export DOCKER_TAG
  export DOCKER_FILE="${__docker_dir}/${DOCKER_FILE}"
  export DOCKER_BASE_IMAGE
  export DOCKER_RUNTIME_IMAGE="${DOCKER_BASE_IMAGE}:${DOCKER_TAG}"

  debug "export DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "export DOCKER_TAG: ${DOCKER_TAG}"
  debug "export DOCKER_FILE: ${DOCKER_FILE}"
  debug "export DOCKER_RUNTIME_IMAGE: ${DOCKER_RUNTIME_IMAGE}"
}


function security_environment () {
  ZIMAGI_DATA_KEY="$1"

  debug "Function: security_environment"
  debug "> ZIMAGI_DATA_KEY: ${ZIMAGI_DATA_KEY}"

  info "Setting certificate environment"
  export ZIMAGI_CA_KEY=$(cat ${__certs_dir}/zimagi-ca.key)
  export ZIMAGI_CA_CERT=$(cat ${__certs_dir}/zimagi-ca.crt)
  export ZIMAGI_KEY=$(cat ${__certs_dir}/zimagi.key)
  export ZIMAGI_CERT=$(cat ${__certs_dir}/zimagi.crt)

  info "Setting encyption keys"
  if [ -z "$ZIMAGI_DATA_KEY" ]; then
    ZIMAGI_DATA_KEY="$(cat ${__certs_dir}/zimagi.crt)"
  fi
  export ZIMAGI_DATA_KEY

  debug "export ZIMAGI_CA_KEY: ${ZIMAGI_CA_KEY}"
  debug "export ZIMAGI_CA_CERT: ${ZIMAGI_CA_CERT}"
  debug "export ZIMAGI_KEY: ${ZIMAGI_KEY}"
  debug "export ZIMAGI_CERT: ${ZIMAGI_CERT}"
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

  docker_environment $DOCKER_RUNTIME $DOCKER_TAG
  security_environment "$DATA_KEY"

  info "Saving Docker configuration ..."
  cat > ${__docker_env_file} <<EOF

# Application configurations
export ZIMAGI_APP_NAME="${APP_NAME}"

export ZIMAGI_DOCKER_FILE="${DOCKER_FILE}"
export ZIMAGI_DOCKER_TAG="${DOCKER_TAG}"
export ZIMAGI_DOCKER_RUNTIME="${DOCKER_RUNTIME}"
export ZIMAGI_DEFAULT_BASE_IMAGE="${DOCKER_BASE_IMAGE}"
export ZIMAGI_DEFAULT_RUNTIME_IMAGE="${DOCKER_RUNTIME_IMAGE}"

# Docker image build arguments
export ZIMAGI_CA_KEY="${ZIMAGI_CA_KEY}"
export ZIMAGI_CA_CERT="${ZIMAGI_CA_CERT}"
export ZIMAGI_KEY="${ZIMAGI_KEY}"
export ZIMAGI_CERT="${ZIMAGI_CERT}"
export ZIMAGI_DATA_KEY="${ZIMAGI_DATA_KEY}"
EOF
  debug ">> ${__docker_env_file}: $(cat ${__docker_env_file})"

  info "Initializing Zimagi environment configuration ..."
  if ! [ -f ${__env_file} ]; then
    cat > ${__env_file} <<EOF

# Minikube configurations
export MINIKUBE_CPUS=${MINIKUBE_CPUS:-2}
export MINIKUBE_KUBERNETES_VERSION="${MINIKUBE_KUBERNETES_VERSION:-1.20.7}"
export MINIKUBE_CONTAINER_RUNTIME="${MINIKUBE_CONTAINER_RUNTIME:-docker}"
export MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-skaffold}"

# Service configurations
export ZIMAGI_COMMAND_HOST_PORT=${ZIMAGI_COMMAND_HOST_PORT:-5123}
export ZIMAGI_DATA_HOST_PORT=${ZIMAGI_DATA_HOST_PORT:-5323}

# Application configurations
export ZIMAGI_LOG_LEVEL="${ZIMAGI_LOG_LEVEL:-warning}"
export ZIMAGI_SECRET_KEY="${ZIMAGI_SECRET_KEY:-XXXXXX20181105}"
export ZIMAGI_POSTGRES_DB="${ZIMAGI_POSTGRES_DB:-zimagi_db}"
export ZIMAGI_POSTGRES_USER="${ZIMAGI_POSTGRES_USER:-zimagi_db_user}"
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
        "ZIMAGI_COMMAND_HOST_PORT"
        "ZIMAGI_DATA_HOST_PORT"
        "ZIMAGI_LOG_LEVEL"
        "ZIMAGI_SECRET_KEY"
        "ZIMAGI_POSTGRES_DB"
        "ZIMAGI_POSTGRES_USER"
        "ZIMAGI_POSTGRES_PASSWORD"
        "ZIMAGI_REDIS_PASSWORD"
    )
    while IFS= read -r variable; do
      if [[ ! " ${ignore_vars[*]} " =~ " ${variable} " ]]; then
        echo "export ${variable}=\"$(printenv $variable)\"" >> ${__env_file}
      fi
    done <<< "$(env | grep -Po "ZIMAGI_[_A-Z0-9]+")"
    info "Zimagi environment configuration saved"
  fi
  debug ">> ${__env_file}: $(cat ${__env_file})"

  info "Importing new Zimagi environment configuration ..."
  import_environment
}


function import_environment () {
  if [ -f ${__env_file} ]; then
    debug "Importing: ${__env_file}"
    source ${__env_file}
  fi
  if [ -f ${__docker_env_file} ]; then
    debug "Importing: ${__docker_env_file}"
    source ${__docker_env_file}
  fi
}
