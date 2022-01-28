#
#=========================================================================================
# <Init> Command
#

function init_usage () {
    cat <<EOF >&2

Initialize Zimagi development environment.

Usage:

  reactor init [<app_name:zimagi>] [flags] [options]

Flags:
${__core_help_flags}

    -e --skip-binary                  Skip downloading binary executables
    -b --skip-build                   Skip Docker image build step
    -u --up                           Startup development environment after initialization

Options:

    --runtime <standard>              Zimagi Docker runtime (standard or nvidia)
    --tag <dev>                       Zimagi Docker tag
    --data-key <0123456789876543210>  Zimagi data encryption key built into Docker image

EOF
  exit 1
}
function init () {
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
      -e|--skip-binary)
      SKIP_BINARY=1
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
  APP_NAME=${APP_NAME:-$DEFAULT_APP_NAME}
  DOCKER_RUNTIME=${DOCKER_RUNTIME:-$DEFAULT_DOCKER_RUNTIME}
  DOCKER_TAG=${DOCKER_TAG:-$DEFAULT_DOCKER_TAG}
  DATA_KEY="${DATA_KEY:-$DEFAULT_DATA_KEY}"
  START_UP=${START_UP:-0}
  SKIP_BUILD=${SKIP_BUILD:-0}
  SKIP_BINARY=${SKIP_BINARY:-0}

  debug "Command: init"
  debug "> APP_NAME: ${APP_NAME}"
  debug "> DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "> DOCKER_TAG: ${DOCKER_TAG}"
  debug "> DATA_KEY: ${DATA_KEY}"
  debug "> START_UP: ${START_UP}"
  debug "> SKIP_BUILD: ${SKIP_BUILD}"
  debug "> SKIP_BINARY: ${SKIP_BINARY}"

  info "Initializing Zimagi folder structure ..."
  create_folder ${__skaffold_dir}
  create_folder ${__binary_dir}
  create_folder ${__data_dir}
  create_folder ${__lib_dir}
  remove_file ${__cli_env_file}

  info "Checking development software requirements ..."
  check_binary docker
  check_binary git
  check_binary curl

  info "Downloading local software dependencies ..."
  if [ $SKIP_BINARY -ne 1 ]; then
    download_binary skaffold "https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64" ${__binary_dir}
    download_binary minikube "https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64" ${__binary_dir}
    download_binary kubectl "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" ${__binary_dir}
  fi

  info "Initializing git repositories ..."
  [[ -d ${__build_dir} ]] || download_git_repo https://github.com/zimagi/build.git ${__build_dir}
  [[ -d ${__certs_dir} ]] || download_git_repo https://github.com/zimagi/certificates.git ${__certs_dir}
  [[ -d ${__charts_dir} ]] || download_git_repo https://github.com/zimagi/charts.git ${__charts_dir}

  info "Initializing Zimagi environment ..."
  init_environment "$APP_NAME" "$DOCKER_RUNTIME" "$DOCKER_TAG" "$DATA_KEY"

  info "Building Zimagi image ..."
  build_image "$SKIP_BUILD"

  info "Zimagi development environment initialization complete"

  if [ $START_UP -eq 1 ]; then
    info "Starting up development environment ..."
    up
  fi
}