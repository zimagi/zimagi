#
#=========================================================================================
# <Test> Command
#

function test_usage () {
    cat <<EOF >&2

Initialize and run Zimagi tests.

Usage:

  reactor test [<script:command>] [flags] [options]

Flags:
${__zimagi_reactor_core_flags}

    -i --init                         Initialize the development environment before testing
    -b --skip-build                   Skip Docker image build step (only applicable with --init option)

Options:

    --name <zimagi>                   Application name or unique namespace on local machine (only applicable with --init option)
    --runtime <standard>              Zimagi Docker runtime (only applicable with --init option)
    --tag <dev>                       Zimagi Docker tag (only applicable with --init option)
    --data-key <0123456789876543210>  Zimagi data encryption key built into Docker image (only applicable with --init option)

EOF
  exit 1
}
function test_command () {
  SCRIPT_NAME=""

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
      test_usage
      ;;
      *)
      if [[ "$1" == "-"* ]] || ! [ -z "$SCRIPT_NAME" ]; then
        error "Unknown argument: ${1}"
        test_usage
      fi
      SCRIPT_NAME="${1}"
      ;;
    esac
    shift
  done
  SCRIPT_NAME="${SCRIPT_NAME:-$DEFAULT_TEST_SCRIPT_NAME}"
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

  debug "Command: test"
  debug "> SCRIPT_NAME: ${SCRIPT_NAME}"
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
  export ZIMAGI_DISPLAY_COLOR="${ZIMAGI_DISPLAY_COLOR:-False}"
  export ZIMAGI_DISABLE_PAGE_CACHE="${ZIMAGI_DISABLE_PAGE_CACHE:-True}"
  export ZIMAGI_TEST_KEY="${ZIMAGI_TEST_KEY:-$DEFAULT_TEST_KEY}"
  export ZIMAGI_STARTUP_SERVICES=${ZIMAGI_STARTUP_SERVICES:-'["scheduler", "worker", "command-api", "data-api"]'}
  #-------------------------------------------------------------------------------

  info "Preparing Zimagi ${DOCKER_RUNTIME}"
  "${__zimagi_dir}"/zimagi env get

  info "Starting Zimagi ${DOCKER_RUNTIME} test script execution"
  "${__zimagi_test_dir}/${SCRIPT_NAME}.sh"
}
