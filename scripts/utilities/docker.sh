#
#=========================================================================================
# Docker Utilities
#

function build_image () {
  USER_PASSWORD="${1}"
  SKIP_BUILD=${2:-0}
  NO_CACHE=${3:-0}

  debug "Function: build_image"
  debug "> USER_PASSWORD: ${USER_PASSWORD}"
  debug "> SKIP_BUILD: ${SKIP_BUILD}"
  debug "> NO_CACHE: ${NO_CACHE}"

  info "Generating certificate environment ..."
  build_environment

  info "Setting up Zimagi package ..."
  cp -f "${__zimagi_app_dir}/VERSION" "${__zimagi_package_dir}/VERSION"

  info "Building Zimagi application image ..."
  find "${__zimagi_app_dir}" -name *.pyc -exec rm -f {} \;
  find "${__zimagi_package_dir}" -name *.pyc -exec rm -f {} \;
  find "${__zimagi_lib_dir}" -name *.pyc -exec rm -f {} \;

  if [ -d "${__zimagi_data_dir}/run" ]; then
    for service_file in "${__zimagi_data_dir}/run"/*.data; do
      if [[ $NO_CACHE -eq 1 ]] || \
        [[ "$service_file" =~ "command-api" ]] || \
        [[ "$service_file" =~ "data-api" ]] || \
        [[ "$service_file" =~ "scheduler" ]] || \
        [[ "$service_file" =~ "controller" ]] || \
        [[ "$service_file" =~ "worker"* ]]; then
        rm -f "$service_file"
      fi
    done
  fi

  if [ $SKIP_BUILD -ne 1 ]; then
    DOCKER_BUILD_VARS=(
      "ZIMAGI_PARENT_IMAGE"
      "ZIMAGI_USER_UID=$(id -u)"
      "ZIMAGI_USER_PASSWORD=${USER_PASSWORD}"
      "ZIMAGI_CA_KEY"
      "ZIMAGI_CA_CERT"
      "ZIMAGI_KEY"
      "ZIMAGI_CERT"
      "ZIMAGI_DATA_KEY"
      "ZIMAGI_DEFAULT_MODULES"
    )

    DOCKER_ARGS=(
      "--file" "$ZIMAGI_DOCKER_FILE"
      "--tag" "$ZIMAGI_DEFAULT_RUNTIME_IMAGE"
      "--platform" "linux/${__architecture}"
    )
    if [ $NO_CACHE -eq 1 ]; then
      DOCKER_ARGS=("${DOCKER_ARGS[@]}" "--no-cache" "--force-rm")
    fi

    for build_var in "${DOCKER_BUILD_VARS[@]}"
    do
      DOCKER_ARGS=("${DOCKER_ARGS[@]}" "--build-arg" "$build_var")
    done
    DOCKER_ARGS=("${DOCKER_ARGS[@]}" "${__zimagi_dir}")

    debug "Docker build arguments"
    debug "${DOCKER_ARGS[@]}"
    docker build "${DOCKER_ARGS[@]}"
  fi
}

function docker_runtime_image () {
  if [ -f "${__zimagi_cli_env_file}" ]
  then
    source "${__zimagi_cli_env_file}"

    if [ -z "$ZIMAGI_RUNTIME_IMAGE" ]
    then
      ZIMAGI_RUNTIME_IMAGE="$ZIMAGI_BASE_IMAGE"
    fi
  else
    ZIMAGI_RUNTIME_IMAGE="$ZIMAGI_DEFAULT_RUNTIME_IMAGE"
  fi

  if ! docker inspect "$ZIMAGI_RUNTIME_IMAGE" >/dev/null 2>&1
  then
    rm -f "${__zimagi_cli_env_file}"
    ZIMAGI_RUNTIME_IMAGE="$ZIMAGI_DEFAULT_RUNTIME_IMAGE"
  fi
  export ZIMAGI_RUNTIME_IMAGE
}

function wipe_docker () {
  info "Stopping and removing all Docker containers ..."
  CONTAINERS=$(docker ps -aq)

  if [ ! -z "$CONTAINERS" ]; then
    docker stop $CONTAINERS >/dev/null 2>&1
    docker rm $CONTAINERS >/dev/null 2>&1
  fi

  info "Removing all Docker networks ..."
  docker network prune -f >/dev/null 2>&1

  info "Removing unused Docker images ..."
  IMAGES=$(docker images --filter dangling=true -qa)

  if [ ! -z "$IMAGES" ]; then
    docker rmi -f $IMAGES >/dev/null 2>&1
  fi

  info "Removing all Docker volumes ..."
  VOLUMES=$(docker volume ls --filter dangling=true -q)

  if [ ! -z "$VOLUMES" ]; then
    docker volume rm $VOLUMES >/dev/null 2>&1
  fi

  info "Cleaning up any remaining Docker images ..."
  IMAGES=$(docker images -qa)

  if [ ! -z "$IMAGES" ]; then
    docker rmi -f $IMAGES >/dev/null 2>&1
  fi

  info "Cleaning Docker build cache ..."
  docker system prune -a -f >/dev/null 2>&1

  info "Removing Docker run definitions and process id files ..."
  rm -Rf "${__zimagi_data_dir}/run"
  rm -f "${__zimagi_data_dir}"/*.pid
}
