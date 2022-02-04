#
#=========================================================================================
# <Test> Command
#

function test_usage () {
    cat <<EOF >&2

Initialize and run Zimagi tests.

Usage:

  reactor test [<script:str:${DEFAULT_TEST_SCRIPT_NAME}>] [flags] [options]

Flags:
${__zimagi_reactor_core_flags}

    -i --init             Initialize the development environment before testing
    -b --skip-build       Skip Docker image build step (requires --init)
    -n --no-cache         Regenerate all intermediate images (requires --init)

Options:

    --name <str>          Application name (requires --init): ${DEFAULT_APP_NAME}
    --runtime <str>       Zimagi Docker runtime (requires --init): ${DEFAULT_DOCKER_RUNTIME}
    --tag <str>           Zimagi Docker tag (requires --init): ${DEFAULT_DOCKER_TAG}
    --password <str>      Zimagi Docker user password (requires --init): ${DEFAULT_USER_PASSWORD}
    --data-key <str>      Zimagi data encryption key (requires --init): ${DEFAULT_DATA_KEY}

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
      -i|--init)
      INITIALIZE=1
      ;;
      -b|--skip-build)
      SKIP_BUILD=1
      ;;
      -n|--no-cache)
      NO_CACHE=1
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
  USER_PASSWORD="${USER_PASSWORD:-$DEFAULT_USER_PASSWORD}"
  DATA_KEY="${DATA_KEY:-$DEFAULT_DATA_KEY}"
  INITIALIZE=${INITIALIZE:-0}
  SKIP_BUILD=${SKIP_BUILD:-0}
  NO_CACHE=${NO_CACHE:-0}

  INIT_ARGS=("$APP_NAME" "--runtime=$DOCKER_RUNTIME" "--tag=$DOCKER_TAG" "--password=$USER_PASSWORD" "--data-key=$DATA_KEY")
  if [ $SKIP_BUILD -ne 0 ]; then
    INIT_ARGS=("${INIT_ARGS[@]}" "--skip-build")
  fi
  if [ $NO_CACHE -ne 0 ]; then
    INIT_ARGS=("${INIT_ARGS[@]}" "--no-cache")
  fi

  debug "Command: test"
  debug "> SCRIPT_NAME: ${SCRIPT_NAME}"
  debug "> APP_NAME: ${APP_NAME}"
  debug "> DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "> DOCKER_TAG: ${DOCKER_TAG}"
  debug "> USER_PASSWORD: ${USER_PASSWORD}"
  debug "> DATA_KEY: ${DATA_KEY}"
  debug "> SKIP_BUILD: ${SKIP_BUILD}"
  debug "> NO_CACHE: ${NO_CACHE}"
  debug "> INITIALIZE: ${INITIALIZE}"
  debug "> INIT ARGS: ${INIT_ARGS[@]}"

  if [[ ! -f "${__zimagi_runtime_env_file}" ]] || [[ $INITIALIZE -eq 1 ]]; then
    init_command "${INIT_ARGS[@]}"
  fi
  #-------------------------------------------------------------------------------
  export ZIMAGI_DISPLAY_COLOR="${ZIMAGI_DISPLAY_COLOR:-False}"
  export ZIMAGI_DISABLE_PAGE_CACHE="${ZIMAGI_DISABLE_PAGE_CACHE:-True}"
  export ZIMAGI_TEST_KEY="${ZIMAGI_TEST_KEY:-$DEFAULT_TEST_KEY}"
  export ZIMAGI_STARTUP_SERVICES=${ZIMAGI_STARTUP_SERVICES:-'["scheduler", "worker", "command-api", "data-api"]'}
  #-------------------------------------------------------------------------------

  info "Preparing Zimagi ${DOCKER_RUNTIME}"
  "${__zimagi_script_dir}"/zimagi env get

  info "Starting Zimagi ${DOCKER_RUNTIME} test script execution"
  "${__zimagi_test_dir}/${SCRIPT_NAME}.sh"
}
