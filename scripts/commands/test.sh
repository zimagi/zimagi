#
#=========================================================================================
# <Test> Command
#

function test_usage () {
    cat <<EOF >&2

Initialize and run Zimagi tests.

Usage:

  reactor test [<type:str:${DEFAULT_TEST_TYPE_NAME}>] [flags] [options]

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
    --admin-key <str>     Zimagi admin user API encryption key (requires --init): ${DEFAULT_ADMIN_API_KEY}
    --admin-token <str>   Zimagi admin user API token (requires --init): ${DEFAULT_ADMIN_API_TOKEN}
    --tags <csv>          Comma separated list of test tags to run
    --exclude-tags <csv>  Comma separated list of test tags to exclude from run

EOF
  exit 1
}
function test_command () {
  TYPE_NAME=""

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
      --admin-key=*)
      ADMIN_API_KEY="${1#*=}"
      ;;
      --admin-key)
      ADMIN_API_KEY="$2"
      shift
      ;;
      --admin-token=*)
      ADMIN_API_TOKEN="${1#*=}"
      ;;
      --admin-token)
      ADMIN_API_TOKEN="$2"
      shift
      ;;
      --tags=*)
      TEST_TAGS="${1#*=}"
      ;;
      --tags)
      TEST_TAGS="$2"
      shift
      ;;
      --exclude-tags=*)
      TEST_EXCLUDE_TAGS="${1#*=}"
      ;;
      --exclude-tags)
      TEST_EXCLUDE_TAGS="$2"
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
      if [[ "$1" == "-"* ]] || ! [ -z "$TYPE_NAME" ]; then
        error "Unknown argument: ${1}"
        test_usage
      fi
      TYPE_NAME="${1}"
      ;;
    esac
    shift
  done
  TYPE_NAME="${TYPE_NAME:-$DEFAULT_TEST_TYPE_NAME}"
  APP_NAME="${APP_NAME:-$DEFAULT_APP_NAME}"
  DOCKER_RUNTIME="${DOCKER_RUNTIME:-$DEFAULT_DOCKER_RUNTIME}"
  DOCKER_TAG="${DOCKER_TAG:-$DEFAULT_DOCKER_TAG}"
  USER_PASSWORD="${USER_PASSWORD:-$DEFAULT_USER_PASSWORD}"
  DATA_KEY="${DATA_KEY:-$DEFAULT_DATA_KEY}"
  ADMIN_API_KEY="${ADMIN_API_KEY:-$DEFAULT_ADMIN_API_KEY}"
  ADMIN_API_TOKEN="${ADMIN_API_TOKEN:-$DEFAULT_ADMIN_API_TOKEN}"
  TEST_TAGS="${TEST_TAGS:-}"
  TEST_EXCLUDE_TAGS="${TEST_EXCLUDE_TAGS:-}"
  INITIALIZE=${INITIALIZE:-0}
  SKIP_BUILD=${SKIP_BUILD:-0}
  NO_CACHE=${NO_CACHE:-0}

  INIT_ARGS=(
    "$APP_NAME"
    "--runtime=$DOCKER_RUNTIME"
    "--tag=$DOCKER_TAG"
    "--password=$USER_PASSWORD"
    "--data-key=$DATA_KEY"
    "--admin-key=$ADMIN_API_KEY"
    "--admin-token=$ADMIN_API_TOKEN"
  )
  if [ $SKIP_BUILD -ne 0 ]; then
    INIT_ARGS=("${INIT_ARGS[@]}" "--skip-build")
  fi
  if [ $NO_CACHE -ne 0 ]; then
    INIT_ARGS=("${INIT_ARGS[@]}" "--no-cache")
  fi

  debug "Command: test"
  debug "> TYPE_NAME: ${TYPE_NAME}"
  debug "> APP_NAME: ${APP_NAME}"
  debug "> DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "> DOCKER_TAG: ${DOCKER_TAG}"
  debug "> USER_PASSWORD: ${USER_PASSWORD}"
  debug "> DATA_KEY: ${DATA_KEY}"
  debug "> ADMIN_API_KEY: ${ADMIN_API_KEY}"
  debug "> ADMIN_API_TOKEN: ${ADMIN_API_TOKEN}"
  debug "> TEST_TAGS: ${TEST_TAGS}"
  debug "> TEST_EXCLUDE_TAGS: ${TEST_EXCLUDE_TAGS}"
  debug "> SKIP_BUILD: ${SKIP_BUILD}"
  debug "> NO_CACHE: ${NO_CACHE}"
  debug "> INITIALIZE: ${INITIALIZE}"
  debug "> INIT ARGS: ${INIT_ARGS[@]}"

  #-------------------------------------------------------------------------------
  export ZIMAGI_DEBUG="${ZIMAGI_DEBUG:-False}"
  export ZIMAGI_DEBUG_COMMAND_PROFILES="${ZIMAGI_DEBUG_COMMAND_PROFILES:-True}"
  export ZIMAGI_LOG_LEVEL="${ZIMAGI_LOG_LEVEL:-warning}"
  export ZIMAGI_DISPLAY_COLOR="${ZIMAGI_DISPLAY_COLOR:-False}"
  export ZIMAGI_DISABLE_PAGE_CACHE="${ZIMAGI_DISABLE_PAGE_CACHE:-True}"
  export ZIMAGI_QUEUE_COMMANDS="${ZIMAGI_QUEUE_COMMANDS:-True}"
  export ZIMAGI_STARTUP_SERVICES=${ZIMAGI_STARTUP_SERVICES:-'["scheduler", "worker", "command-api", "data-api"]'}

  export ZIMAGI_SERVER_WORKERS=${ZIMAGI_SERVER_WORKERS:-2}
  export ZIMAGI_WORKER_MAX_PROCESSES=${ZIMAGI_WORKER_MAX_PROCESSES:-3}

  export ZIMAGI_ENCRYPT_DATA_API="${ZIMAGI_ENCRYPT_DATA_API:-True}"
  export ZIMAGI_ENCRYPT_COMMAND_API="${ZIMAGI_ENCRYPT_COMMAND_API:-True}"
  export ZIMAGI_ADMIN_API_KEY="$ADMIN_API_KEY"
  #-------------------------------------------------------------------------------

  docker_environment "$DOCKER_RUNTIME" "$DOCKER_TAG"

  if [[ ! -f "${__zimagi_runtime_env_file}" ]] || [[ $INITIALIZE -eq 1 ]]; then
    init_command "${INIT_ARGS[@]}"
  fi

  echo "Zimagi ${DOCKER_RUNTIME} ${TYPE_NAME} environment"
  "${__zimagi_dir}"/zimagi env get

  TEST_ARGS=()
  if [ ! -z "$TEST_TAGS" ]; then
    TEST_ARGS=("${TEST_ARGS[@]}" "--tags="${TEST_TAGS}"")
  fi
  if [ ! -z "$TEST_EXCLUDE_TAGS" ]; then
    TEST_ARGS=("${TEST_ARGS[@]}" "--exclude-tags="${TEST_EXCLUDE_TAGS}"")
  fi

  echo "Running Zimagi ${DOCKER_RUNTIME} ${TYPE_NAME} tests"
  "${__zimagi_dir}"/zimagi test --types="${TYPE_NAME}" "${TEST_ARGS[@]}"
}
