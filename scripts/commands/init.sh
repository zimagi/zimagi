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

    --skip-build          Skip Docker image build step
    --no-cache            Regenerate all intermediate images
    --no-update           Disable the cluster image update

Options:

    --runtime <str>       Zimagi Docker runtime (standard or nvidia): ${DEFAULT_DOCKER_RUNTIME}
    --tag <str>           Zimagi Docker tag: ${DEFAULT_DOCKER_TAG}
    --password <str>      Zimagi Docker user password: ${DEFAULT_USER_PASSWORD}
    --data-key <str>      Zimagi data encryption key: ${DEFAULT_DATA_KEY}
    --admin-key <str>     Zimagi admin user API encryption key: ${DEFAULT_ADMIN_API_KEY}
    --admin-token <str>   Zimagi admin user API token: ${DEFAULT_ADMIN_API_TOKEN}
    --cert-subject <str>  Self signed ingress SSL certificate subject: ${DEFAULT_CERT_SUBJECT}
    --cert-days <int>     Self signed ingress SSL certificate days to expiration: ${DEFAULT_CERT_DAYS}

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
      --cert-days=*)
      CERT_DAYS="${1#*=}"
      ;;
      --cert-days)
      CERT_DAYS="$2"
      shift
      ;;
      --cert-subject=*)
      CERT_SUBJECT="${1#*=}"
      ;;
      --cert-subject)
      CERT_SUBJECT="$2"
      shift
      ;;
      --skip-build)
      SKIP_BUILD=1
      ;;
      --no-cache)
      NO_CACHE=1
      ;;
      --no-update)
      NO_UPDATE=1
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
  DOCKER_TAG="${DOCKER_TAG:-"${DEFAULT_DOCKER_TAG}-$(date +%s)"}"
  USER_PASSWORD="${USER_PASSWORD:-$DEFAULT_USER_PASSWORD}"
  DATA_KEY="${DATA_KEY:-$DEFAULT_DATA_KEY}"
  ADMIN_API_KEY="${ADMIN_API_KEY:-$DEFAULT_ADMIN_API_KEY}"
  ADMIN_API_TOKEN="${ADMIN_API_TOKEN:-$DEFAULT_ADMIN_API_TOKEN}"
  SKIP_BUILD=${SKIP_BUILD:-0}
  NO_CACHE=${NO_CACHE:-0}
  NO_UPDATE=${NO_UPDATE:-0}
  CERT_SUBJECT="${CERT_SUBJECT:-$DEFAULT_CERT_SUBJECT}"
  CERT_DAYS="${CERT_DAYS:-$DEFAULT_CERT_DAYS}"

  debug "Command: init"
  debug "> APP_NAME: ${APP_NAME}"
  debug "> DOCKER_RUNTIME: ${DOCKER_RUNTIME}"
  debug "> DOCKER_TAG: ${DOCKER_TAG}"
  debug "> USER_PASSWORD: ${USER_PASSWORD}"
  debug "> DATA_KEY: ${DATA_KEY}"
  debug "> ADMIN_API_KEY: ${ADMIN_API_KEY}"
  debug "> ADMIN_API_TOKEN: ${ADMIN_API_TOKEN}"
  debug "> SKIP_BUILD: ${SKIP_BUILD}"
  debug "> NO_CACHE: ${NO_CACHE}"
  debug "> NO_UPDATE: ${NO_UPDATE}"
  debug "> CERT_SUBJECT: ${CERT_SUBJECT}"
  debug "> CERT_DAYS: ${CERT_DAYS}"

  info "Initializing Zimagi environment ..."
  init_environment "$APP_NAME" "$DOCKER_RUNTIME" "$DOCKER_TAG" "$USER_PASSWORD" "$DATA_KEY" "$ADMIN_API_KEY" "$ADMIN_API_TOKEN"
  remove_file "${__zimagi_cli_env_file}"

  info "Checking development software requirements ..."
  check_binary docker
  check_binary git
  check_binary curl
  check_binary openssl

  info "Downloading local software dependencies ..."
  download_binary minikube "https://storage.googleapis.com/minikube/releases/latest/minikube-${__os}-${__architecture}" "${__zimagi_binary_dir}"
  download_binary kubectl "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/${__os}/${__architecture}/kubectl" "${__zimagi_binary_dir}"
  download_binary helm "https://get.helm.sh/helm-v${HELM_VERSION}-${__os}-${__architecture}.tar.gz" "${__zimagi_binary_dir}" "${__os}-${__architecture}"
  download_binary argocd "https://github.com/argoproj/argo-cd/releases/latest/download/argocd-${__os}-${__architecture}" "${__zimagi_binary_dir}"

  info "Initializing git repositories ..."
  download_git_repo https://github.com/zimagi/charts.git "${__zimagi_charts_dir}"
  download_git_repo https://github.com/zimagi/argocd-apps.git "${__zimagi_argocd_apps_dir}"

  info "Generating ingress certificates ..."
  generate_certs "${CERT_SUBJECT}/CN=*.$(echo "$ZIMAGI_APP_NAME" | tr '_' '-').local" "$CERT_DAYS"

  info "Building Zimagi image ..."
  build_image "$USER_PASSWORD" "$SKIP_BUILD" "$NO_CACHE"

  if [ $NO_UPDATE -eq 0 ]; then
    update_command --image
  fi

  info "Zimagi development environment initialization complete"
}
