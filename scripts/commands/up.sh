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

    --init                Initialize the development environment before startup
    --skip-build          Skip Docker image build step (requires --init)
    --no-cache            Regenerate all intermediate images (requires --init)

Options:

    --name <str>          Application name (requires --init): ${DEFAULT_APP_NAME}
    --runtime <str>       Zimagi Docker runtime (requires --init): ${DEFAULT_DOCKER_RUNTIME}
    --tag <str>           Zimagi Docker tag (requires --init): ${DEFAULT_DOCKER_TAG}
    --password <str>      Zimagi Docker user password (requires --init): ${DEFAULT_USER_PASSWORD}
    --data-key <str>      Zimagi data encryption key (requires --init): ${DEFAULT_DATA_KEY}
    --admin-key <str>     Zimagi admin user API encryption key (requires --init): ${DEFAULT_ADMIN_API_KEY}
    --admin-token <str>   Zimagi admin user API token (requires --init): ${DEFAULT_ADMIN_API_TOKEN}

EOF
  exit 1
}

function up_command () {
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
      --init)
      INITIALIZE=1
      ;;
      --skip-build)
      SKIP_BUILD=1
      ;;
      --no-cache)
      NO_CACHE=1
      ;;
      -h|--help)
      up_usage
      ;;
      *)
      if ! [ -z "$1" ]; then
        error "Unknown argument: ${1}"
        up_usage
      fi
      ;;
    esac
    shift
  done
  APP_NAME="${APP_NAME:-$DEFAULT_APP_NAME}"
  DOCKER_RUNTIME="${DOCKER_RUNTIME:-$DEFAULT_DOCKER_RUNTIME}"
  DOCKER_TAG="${DOCKER_TAG:-$DEFAULT_DOCKER_TAG}"
  USER_PASSWORD="${USER_PASSWORD:-$DEFAULT_USER_PASSWORD}"
  DATA_KEY="${DATA_KEY:-$DEFAULT_DATA_KEY}"
  ADMIN_API_KEY="${ADMIN_API_KEY:-$DEFAULT_ADMIN_API_KEY}"
  ADMIN_API_TOKEN="${ADMIN_API_TOKEN:-$DEFAULT_ADMIN_API_TOKEN}"
  INITIALIZE=${INITIALIZE:-0}
  SKIP_BUILD=${SKIP_BUILD:-0}
  NO_CACHE=${NO_CACHE:-0}

  INIT_ARGS=(
    "$APP_NAME"
    "--no-update"
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

  debug "Command: up"
  debug "> APP_NAME: ${APP_NAME}"
  debug "> DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "> DOCKER_TAG: ${DOCKER_TAG}"
  debug "> USER_PASSWORD: ${USER_PASSWORD}"
  debug "> DATA_KEY: ${DATA_KEY}"
  debug "> ADMIN_API_KEY: ${ADMIN_API_KEY}"
  debug "> ADMIN_API_TOKEN: ${ADMIN_API_TOKEN}"
  debug "> SKIP_BUILD: ${SKIP_BUILD}"
  debug "> NO_CACHE: ${NO_CACHE}"
  debug "> INITIALIZE: ${INITIALIZE}"
  debug "> INIT ARGS: ${INIT_ARGS[@]}"

  if [[ ! -f "${__zimagi_runtime_env_file}" ]] || [[ $INITIALIZE -eq 1 ]]; then
    init_command "${INIT_ARGS[@]}"
  fi
  #-------------------------------------------------------------------------------
  export ZIMAGI_STARTUP_SERVICES=${ZIMAGI_STARTUP_SERVICES:-'["scheduler", "controller", "command-api", "data-api", "flower"]'}
  #-------------------------------------------------------------------------------

  "${__zimagi_dir}/zimagi" env get

  start_minikube
  launch_minikube_tunnel

  info "Updating cluster applications ..."
  update_command

  info "Updating Zimagi local host ..."
  "${__zimagi_dir}/zimagi" host save local \
   host="localhost"

  info "Updating Zimagi kube host ..."
  "${__zimagi_dir}/zimagi" host save kube \
   host="zimagi-cmd.$(echo "$ZIMAGI_APP_NAME" | tr '_' '-').local" \
   command_port=443

  launch_minikube_dashboard
}
