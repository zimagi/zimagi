#
#=========================================================================================
# Environment Generators
#

function zimagi_docker_environment () {
  ZIMAGI_BASE_IMAGE="${ZIMAGI_BASE_IMAGE:-$DEFAULT_ZIMAGI_BASE_IMAGE}"
  ZIMAGI_DOCKER_RUNTIME="${ZIMAGI_DOCKER_RUNTIME:-$DEFAULT_ZIMAGI_DOCKER_RUNTIME}"
  ZIMAGI_DOCKER_TAG="${ZIMAGI_DOCKER_TAG:-$DEFAULT_ZIMAGI_DOCKER_TAG}"

  debug "Setting Docker environment ..."
  debug "> ZIMAGI_BASE_IMAGE: ${ZIMAGI_BASE_IMAGE}"
  debug "> ZIMAGI_DOCKER_RUNTIME: ${ZIMAGI_DOCKER_RUNTIME}"
  debug "> ZIMAGI_DOCKER_TAG: ${ZIMAGI_DOCKER_TAG}"

  if [ "$ZIMAGI_DOCKER_RUNTIME" == "standard" ]; then
    ZIMAGI_PARENT_IMAGE="$ZIMAGI_STANDARD_PARENT_IMAGE"
  else
    ZIMAGI_DOCKER_TAG="${ZIMAGI_DOCKER_RUNTIME}-${ZIMAGI_DOCKER_TAG}"

    if [ "$ZIMAGI_DOCKER_RUNTIME" == "nvidia" ]; then
      ZIMAGI_PARENT_IMAGE="$ZIMAGI_NVIDIA_PARENT_IMAGE"
    else
      emergency "Zimagi Docker runtime not supported: ${ZIMAGI_DOCKER_RUNTIME}"
    fi
  fi

  export ZIMAGI_DOCKER_GROUP="999"
  export ZIMAGI_DOCKER_RUNTIME
  export ZIMAGI_DOCKER_TAG
  export ZIMAGI_PARENT_IMAGE
  export ZIMAGI_BASE_IMAGE
  export ZIMAGI_DEFAULT_RUNTIME_IMAGE="${ZIMAGI_BASE_IMAGE}:${ZIMAGI_DOCKER_TAG}"

  debug "export ZIMAGI_DOCKER_GROUP: ${ZIMAGI_DOCKER_GROUP}"
  debug "export ZIMAGI_DOCKER_RUNTIME: ${ZIMAGI_DOCKER_RUNTIME}"
  debug "export ZIMAGI_DOCKER_TAG: ${ZIMAGI_DOCKER_TAG}"
  debug "export ZIMAGI_PARENT_IMAGE: ${ZIMAGI_PARENT_IMAGE}"
  debug "export ZIMAGI_BASE_IMAGE: ${ZIMAGI_BASE_IMAGE}"
  debug "export ZIMAGI_DEFAULT_RUNTIME_IMAGE: ${ZIMAGI_DEFAULT_RUNTIME_IMAGE}"
}

function zimagi_security_environment () {
  debug "Setting security environment ..."
  export ZIMAGI_USER_PASSWORD="${ZIMAGI_USER_PASSWORD:-$DEFAULT_ZIMAGI_USER_PASSWORD}"
  export ZIMAGI_SECRET_KEY="${ZIMAGI_SECRET_KEY:-$DEFAULT_ZIMAGI_SECRET_KEY}"
  export ZIMAGI_DATA_KEY="${ZIMAGI_DATA_KEY:-$DEFAULT_ZIMAGI_DATA_KEY}"
  export ZIMAGI_ADMIN_API_KEY="${ZIMAGI_ADMIN_API_KEY:-$DEFAULT_ZIMAGI_ADMIN_API_KEY}"
  export ZIMAGI_ADMIN_API_TOKEN="${ZIMAGI_ADMIN_API_TOKEN:-$DEFAULT_ZIMAGI_ADMIN_API_TOKEN}"

  debug "export ZIMAGI_USER_PASSWORD: ${ZIMAGI_USER_PASSWORD}"
  debug "export ZIMAGI_SECRET_KEY: ${ZIMAGI_SECRET_KEY}"
  debug "export ZIMAGI_DATA_KEY: ${ZIMAGI_DATA_KEY}"
  debug "export ZIMAGI_ADMIN_API_KEY: ${ZIMAGI_ADMIN_API_KEY}"
  debug "export ZIMAGI_ADMIN_API_TOKEN: ${ZIMAGI_ADMIN_API_TOKEN}"
}

function zimagi_environment () {
  debug "Initializing Zimagi environment ..."
  zimagi_docker_environment
  zimagi_security_environment
}
