#
#=========================================================================================
# <Init> Command
#

function init_usage () {
    cat <<EOF >&2

Initialize Zimagi development environment.

Usage:

  reactor init [<app_name:str:${DEFAULT_APP_NAME}>] [flags] [options]

Flags:
${__zimagi_reactor_core_flags}

    -b --skip-build       Skip Docker image build step
    -n --no-cache         Regenerate all intermediate images
    -u --up               Startup development environment after initialization

Options:

    --runtime <str>       Zimagi Docker runtime (standard or nvidia): ${DEFAULT_DOCKER_RUNTIME}
    --tag <str>           Zimagi Docker tag: ${DEFAULT_DOCKER_TAG}
    --password <str>      Zimagi Docker user password: ${DEFAULT_USER_PASSWORD}
    --data-key <str>      Zimagi data encryption key: ${DEFAULT_DATA_KEY}

EOF
  exit 1
}
function init_command () {
  APP_NAME=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --runtime=*)
      DOCKER_RUNTIME="${1#*=}"
      ;;
      --runtime)
      DOCKER_RUNTIME="$2"
      shift
      ;;
      --tag=*)
      DOCKER_TAG="${1#*=}"
      ;;
      --tag)
      DOCKER_TAG="$2"
      shift
      ;;
      --password=*)
      USER_PASSWORD="${1#*=}"
      ;;
      --password)
      USER_PASSWORD="$2"
      shift
      ;;
      --data-key=*)
      DATA_KEY="${1#*=}"
      ;;
      --data-key)
      DATA_KEY="$2"
      shift
      ;;
      -u|--up)
      START_UP=1
      ;;
      -b|--skip-build)
      SKIP_BUILD=1
      ;;
      -n|--no-cache)
      NO_CACHE=1
      ;;
      -h|--help)
      init_usage
      ;;
      *)
      if [[ "$1" == "-"* ]] || ! [ -z "$APP_NAME" ]; then
        error "Unknown argument: ${1}"
        init_usage
      fi
      APP_NAME="${1}"
      ;;
    esac
    shift
  done
  APP_NAME="${APP_NAME:-$DEFAULT_APP_NAME}"
  DOCKER_RUNTIME="${DOCKER_RUNTIME:-$DEFAULT_DOCKER_RUNTIME}"
  DOCKER_TAG="${DOCKER_TAG:-$DEFAULT_DOCKER_TAG}"
  USER_PASSWORD="${USER_PASSWORD:-$DEFAULT_USER_PASSWORD}"
  DATA_KEY="${DATA_KEY:-$DEFAULT_DATA_KEY}"
  START_UP=${START_UP:-0}
  SKIP_BUILD=${SKIP_BUILD:-0}
  NO_CACHE=${NO_CACHE:-0}

  debug "Command: init"
  debug "> APP_NAME: ${APP_NAME}"
  debug "> DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "> DOCKER_TAG: ${DOCKER_TAG}"
  debug "> USER_PASSWORD: ${USER_PASSWORD}"
  debug "> DATA_KEY: ${DATA_KEY}"
  debug "> START_UP: ${START_UP}"
  debug "> SKIP_BUILD: ${SKIP_BUILD}"
  debug "> NO_CACHE: ${NO_CACHE}"

  info "Initializing Zimagi environment ..."
  init_environment "$APP_NAME" "$DOCKER_RUNTIME" "$DOCKER_TAG" "$USER_PASSWORD" "$DATA_KEY"

  info "Initializing Zimagi folder structure ..."
  create_folder "${__zimagi_binary_dir}"
  create_folder "${__zimagi_data_dir}"
  create_folder "${__zimagi_lib_dir}"
  remove_file "${__zimagi_cli_env_file}"

  info "Checking development software requirements ..."
  check_binary docker
  check_binary git
  check_binary curl
  check_binary openssl

  info "Downloading local software dependencies ..."
  download_binary skaffold "https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64" "${__zimagi_binary_dir}"
  download_binary minikube "https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64" "${__zimagi_binary_dir}"
  download_binary kubectl "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" "${__zimagi_binary_dir}"
  install_helm

  info "Initializing git repositories ..."
  [[ -d "${__zimagi_build_dir}" ]] || download_git_repo https://github.com/zimagi/build.git "${__zimagi_build_dir}"
  [[ -d "${__zimagi_certs_dir}" ]] || download_git_repo https://github.com/zimagi/certificates.git "${__zimagi_certs_dir}"
  [[ -d "${__zimagi_charts_dir}" ]] || download_git_repo https://github.com/zimagi/charts.git "${__zimagi_charts_dir}"

  info "Building Zimagi image ..."
  build_image "$USER_PASSWORD" "$SKIP_BUILD" "$NO_CACHE"

  info "Zimagi development environment initialization complete"

  if [ $START_UP -eq 1 ]; then
    info "Starting up development environment ..."
    up
  fi
}
