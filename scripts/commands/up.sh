#
#=========================================================================================
# <Up> Command
#

function up_usage () {
    cat <<EOF >&2

Initialize and ensure Zimagi development environment is running.

Usage:

  reactor up [flags] [options]

Flags:
${__zimagi_reactor_core_flags}

    -i --init                         Initialize the development environment before startup
    -b --skip-build                   Skip Docker image build step (only applicable with --init option)

Options:

    --name <zimagi>                   Application name or unique namespace on local machine (only applicable with --init option)
    --runtime <standard>              Zimagi Docker runtime (only applicable with --init option)
    --tag <dev>                       Zimagi Docker tag (only applicable with --init option)
    --data-key <0123456789876543210>  Zimagi data encryption key built into Docker image (only applicable with --init option)

EOF
  exit 1
}
function up () {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --name=*)
      APP_NAME="${1#*=}"
      ;;
      --name)
      APP_NAME="$2"
      shift
      ;;
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
      -i|--init)
      INITIALIZE=1
      ;;
      -b|--skip-build)
      SKIP_BUILD=1
      ;;
      -h|--help)
      up_usage
      ;;
      *)
      error "Unknown argument: ${1}"
      up_usage
      ;;
    esac
    shift
  done
  APP_NAME="${APP_NAME:-$DEFAULT_APP_NAME}"
  DOCKER_RUNTIME="${DOCKER_RUNTIME:-$DEFAULT_DOCKER_RUNTIME}"
  DOCKER_TAG="${DOCKER_TAG:-$DEFAULT_DOCKER_TAG}"
  DATA_KEY="${DATA_KEY:-$DEFAULT_DATA_KEY}"
  INITIALIZE=${INITIALIZE:-0}
  SKIP_BUILD=${SKIP_BUILD:-0}

  INIT_ARGS=("$APP_NAME" "--runtime=$DOCKER_RUNTIME" "--tag=$DOCKER_TAG" "--data-key=$DATA_KEY")
  if [ $SKIP_BUILD -ne 0 ]; then
    INIT_ARGS=("${INIT_ARGS[@]}" "--skip-build")
  fi

  debug "Command: up"
  debug "> APP_NAME: ${APP_NAME}"
  debug "> DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "> DOCKER_TAG: ${DOCKER_TAG}"
  debug "> DATA_KEY: ${DATA_KEY}"
  debug "> SKIP_BUILD: ${SKIP_BUILD}"
  debug "> INITIALIZE: ${INITIALIZE}"
  debug "> INIT ARGS: ${INIT_ARGS[@]}"

  if [[ ! -f "${__zimagi_runtime_env_file}" ]] || [[ $INITIALIZE -eq 1 ]]; then
    init "${INIT_ARGS[@]}"
  fi
  #-------------------------------------------------------------------------------
  export ZIMAGI_STARTUP_SERVICES=${ZIMAGI_STARTUP_SERVICES:-'["scheduler", "worker", "command-api", "data-api"]'}
  #-------------------------------------------------------------------------------

  "${__zimagi_dir}"/zimagi env get

  start_minikube
  start_skaffold
  # Nothing can come after start_skaffold command
}
