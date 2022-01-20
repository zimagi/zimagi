#!/usr/bin/env bash
#
# Usage:
#
#  LOG_LEVEL=7 ./reactor.sh up --init=true

# Exit on error. Append "|| true" if you expect an error.
set -o errexit
# Exit on error inside any functions or subshells.
set -o errtrace
# Do not allow use of undefined vars. Use ${VAR:-} to use an undefined VAR
set -o nounset
# Catch the error in case mysqldump fails (but gzip succeeds) in `mysqldump |gzip`
set -o pipefail
# Turn on traces, useful while debugging but commented out by default
# set -o xtrace

source reactorfile

# Set magic variables for current file, directory, os, etc.
__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
__file="${__dir}/$(basename "${BASH_SOURCE[0]}")"
__base="$(basename "${__file}" .sh)"
__skaffold_dir="${SKAFFOLD_DIR:-${__dir}/.skaffold}"
__binaries_dir="${__skaffold_dir}/bins"
__charts_dir="${__dir}/charts"
__certs_dir="${__dir}/certs"
# shellcheck disable=SC2034,SC2015
__invocation="$(printf %q "${__file}")$( (($#)) && printf ' %q' "$@" || true)"

# Define the environment variables (and their defaults) that this script depends on
LOG_LEVEL="${LOG_LEVEL:-6}" # 7 = debug -> 0 = emergency
NO_COLOR="${NO_COLOR:-}"    # true = disable color. otherwise autodetected
MINIKUBE_CPUS=${MINIKUBE_CPUS:-2}
MINIKUBE_KUBERNETES_VERSION=${MINIKUBE_KUBERNETES_VERSION:-1.20.7}
MINIKUBE_CONTAINER_RUNTIME=${MINIKUBE_CONTAINER_RUNTIME:-docker}
MINIKUBE_PROFILE=${MINIKUBE_PROFILE:-skaffold}
COMMAND_API_PORT=${COMMAND_API_PORT:-5123}
DATA_API_PORT=${DATA_API_PORT:-5323}

function __log () {
  local log_level="${1}"
  shift

  # shellcheck disable=SC2034
  local color_debug="\\x1b[35m"
  # shellcheck disable=SC2034
  local color_info="\\x1b[32m"
  # shellcheck disable=SC2034
  local color_notice="\\x1b[34m"
  # shellcheck disable=SC2034
  local color_warning="\\x1b[33m"
  # shellcheck disable=SC2034
  local color_error="\\x1b[31m"
  # shellcheck disable=SC2034
  local color_critical="\\x1b[1;31m"
  # shellcheck disable=SC2034
  local color_alert="\\x1b[1;37;41m"
  # shellcheck disable=SC2034
  local color_emergency="\\x1b[1;4;5;37;41m"

  local colorvar="color_${log_level}"

  local color="${!colorvar:-${color_error}}"
  local color_reset="\\x1b[0m"

  if [[ "${NO_COLOR:-}" = "true" ]] || { [[ "${TERM:-}" != "xterm"* ]] && [[ "${TERM:-}" != "screen"* ]]; } || [[ ! -t 2 ]]; then
    if [[ "${NO_COLOR:-}" != "false" ]]; then
      # Don't use colors on pipes or non-recognized terminals
      color=""; color_reset=""
    fi
  fi

  # all remaining arguments are to be printed
  local log_line=""

  while IFS=$'\n' read -r log_line; do
    echo -e "$(date -u +"%Y-%m-%d %H:%M:%S UTC") ${color}$(printf "[%9s]" "${log_level}")${color_reset} ${log_line}" 1>&2
  done <<< "${@:-}"
}

function emergency () {                               __log emergency "${@}"; exit 1; }
function alert ()     { [[ "${LOG_LEVEL:-0}" -ge 1 ]] && __log alert "${@}"; true; }
function critical ()  { [[ "${LOG_LEVEL:-0}" -ge 2 ]] && __log critical "${@}"; true; }
function error ()     { [[ "${LOG_LEVEL:-0}" -ge 3 ]] && __log error "${@}"; true; }
function warning ()   { [[ "${LOG_LEVEL:-0}" -ge 4 ]] && __log warning "${@}"; true; }
function notice ()    { [[ "${LOG_LEVEL:-0}" -ge 5 ]] && __log notice "${@}"; true; }
function info ()      { [[ "${LOG_LEVEL:-0}" -ge 6 ]] && __log info "${@}"; true; }
function debug ()     { [[ "${LOG_LEVEL:-0}" -ge 7 ]] && __log debug "${@}"; true; }

function help () {
  echo "" 1>&2
  echo " ${*}" 1>&2
  echo "" 1>&2
  echo "  ${__usage:-No usage available}" 1>&2
  echo "" 1>&2

  if [[ "${__helptext:-}" ]]; then
    echo " ${__helptext}" 1>&2
    echo "" 1>&2
  fi

  exit 1
}

# shellcheck disable=SC2015
[[ "${__usage+x}" ]] || read -r -d '' __usage <<-'EOF' || true
  Reactor levarages Zimagi local development environment.

  Usage:
    ${filename} [flags] [commands]

  Flags:
    -v --verbose     Enable verbose mode, print script as it is executed
    -d --debug       Enables debug mode
    -n --no-color    Disable color output
    -h --help        Display helm message

  Commands:
    init             Initialise development environment
    up               Start development environment
    down             Stop development environment
    destroy          Purge development environment
    global-status    Output status of the development environment
    ssh              Connects to running application
    reload           Reload command and data api
EOF

[[ "${__helptext+x}" ]] || read -r -d '' __helptext <<-'EOF' ||
  Use "reactor <command> --help" for more information about a given command.
EOF

[[ $# -eq 0 ]] && arg_h=1

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
    -v|--verbose)
      arg_v=1
      shift
      ;;
    -d|--debug)
      arg_d=1
      shift
      ;;
    -n|--no-color)
      arg_n=1
      shift
      ;;
    -h|--help)
      arg_h=1
      shift
      ;;
    *)
      POSITIONAL+=("$1") # save it in an array for later
      shift # past argument
      ;;
  esac
done

set -- "${POSITIONAL[@]}"

function __cleanup_before_exit () {
  # unset DOCKER_TLS_VERIFY="1"
  # usnet DOCKER_HOST="tcp://192.168.49.2:2376"
  # unset DOCKER_CERT_PATH="/home/jagyugyaerik/.minikube/certs"
  # unset MINIKUBE_ACTIVE_DOCKERD="minikube"
  # unset ZIMAGI_CA_KEY=$(cat ${__certs_dir}/zimagi-ca.key)
  # unset ZIMAGI_CA_CERT=$(cat ${__certs_dir}/zimagi-ca.crt)
  # unset ZIMAGI_KEY=$(cat ${__certs_dir}/zimagi.key)
  # unset ZIMAGI_CERT=$(cat ${__certs_dir}/zimagi.crt)
  info "Cleaning up. Done"
}

trap __cleanup_before_exit EXIT

# requires `set -o errtrace`
__err_report() {
    local error_code=${?}
    error "Error in ${__file} in function ${1} on line ${2}"
    exit ${error_code}
}

# debug mode
if [[ "${arg_d:-0}" = "1" ]]; then
  set -o xtrace
  PS4='+(${BASH_SOURCE}:${LINENO}): ${FUNCNAME[0]:+${FUNCNAME[0]}(): }'
  LOG_LEVEL="7"
  # Enable error backtracing
  trap '__err_report "${FUNCNAME:-.}" ${LINENO}' ERR
fi

# verbose mode
if [[ "${arg_v:-0}" = "1" ]]; then
  set -o verbose
fi

# no color mode
if [[ "${arg_n:-0}" = "1" ]]; then
  NO_COLOR="true"
fi

# help mode
if [[ "${arg_h:-0}" = "1" ]]; then
  # Help exists with code 1
  help "Help using ${0}"
fi

check_binary () {
  if ! command -v "$1" > /dev/null; then
    emergency "Install binary: \"$1\""
  fi
}

create_folder () {
  if ! [ -d "$1" ]; then
    debug "Create folder \"$1\""
    mkdir -p "$1"
  fi
}

download_binary () {
  if ! command -v "$3/$1" > /dev/null; then
    debug "Download binary: \"$1\" from url: \"$2\""
    curl -sLo "$1" "$2"
    debug "\"$1\" was downloaded install binary into folder: \"$3\""
    install "$1" "$3"
  fi
}

download_git_repo () {
  DEPTH=${4:-1}
  [[ -d "$2" ]] && rm -rf $2
  info "Downloading repo \"$1\" into folder \"$2\" ..."
  git clone --quiet --depth=$DEPTH "$1" "$2"
}

function init_step() {
  debug "Command: init"
  info "Creating folder structure ..."
  create_folder ${__skaffold_dir}
  create_folder ${__binaries_dir}
  info "Folder structure is done."

  info "Checking global software requirements ..."
  check_binary "docker"
  check_binary "git"
  check_binary "curl"
  info "Global software requirements are done."

  info "Downloading local software dependencies ..."
  download_binary "skaffold" "https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64" "$__binaries_dir"
  download_binary "minikube" "https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64" "$__binaries_dir"
  download_binary "kubectl" "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" "$__binaries_dir"
  info "Local software depencies were downloaded."

  info "Download git repos ..."
  [[ -d ${__charts_dir} ]] || download_git_repo git@github.com:zimagi/charts.git ${__charts_dir}
  [[ -d ${__certs_dir} ]] || download_git_repo git@github.com:zimagi/certificates.git ${__certs_dir}
  info "Git repos are done"
}

function start_minikube() {
  debug "Start minikube ..."
  exit_code=$($__binaries_dir/minikube start --driver=docker --cpus=$MINIKUBE_CPUS --kubernetes-version=$MINIKUBE_KUBERNETES_VERSION --container-runtime=$MINIKUBE_CONTAINER_RUNTIME)
  debug "exit code: ${exit_code}"
}

start_skaffold () {
  eval $(minikube docker-env)
  export ZIMAGI_CA_KEY=$(cat ${__certs_dir}/zimagi-ca.key)
  export ZIMAGI_CA_CERT=$(cat ${__certs_dir}/zimagi-ca.crt)
  export ZIMAGI_KEY=$(cat ${__certs_dir}/zimagi.key)
  export ZIMAGI_CERT=$(cat ${__certs_dir}/zimagi.crt)
  export DOCKER_RUNTIME=standard
  $__binaries_dir/skaffold dev --port-forward
}

function up_step() {
  init_step
  info "Start development environment ..."
  debug "Starting minikube ..."
  start_minikube
  debug "Minikube has started"
  debug "Starting skaffold ..."
  start_skaffold
}

function down_step() {
  info "Stop development environment ..."
  if ! $(${__binaries_dir}/minikube status > /dev/null); then
    ${__binaries_dir}/minikube stop
  fi
}

function destroy_step() {
  info "Tear down development environment ..."
  minikube delete --purge
}

function global_status() {
    info "global-status"
    if ! $($__binaries_dir/minikube status > /dev/null); then
      emergency "Minikube is not running"
    fi
    echo
    $__binaries_dir/minikube status
    $__binaries_dir/kubectl get pods -l 'app.kubernetes.io/name=zimagi'
    echo
}

function reload_step() {
  COMMAND_API_POD=$($__binaries_dir/kubectl get pods -l 'app.kubernetes.io/component=command-api' -o=jsonpath='{.items[*].metadata.name}' )
  DATA_API_POD=$($__binaries_dir/kubectl get pods -l 'app.kubernetes.io/component=data-api' -o=jsonpath='{.items[*].metadata.name}' )
  PODS=$(printf "%s %s" $COMMAND_API_POD $DATA_API_POD)
  info "reload pods ${PODS}"
  for pod in $PODS; do
    kubectl delete pod $pod &
  done
}

function kex_pod() {
  if ! $($__binaries_dir/minikube status > /dev/null); then
    emergency "There is no minikube running"
  fi
  PODS=($($__binaries_dir/kubectl get pods -l 'app.kubernetes.io/name=zimagi' -o=jsonpath='{.items[*].metadata.name}' ))
  if ! [ ${#PODS[@]} -eq 0 ]; then
    for index in $(seq 1 ${#PODS[@]}); do
      echo "${index}.) ${PODS[$index - 1]}"
    done
    read -p "Enter number: " POD_INPUT
    kubectl exec -ti ${PODS[$POD_INPUT-1]} bash
  else
    alert "Zimagi is not running"
  fi
}

[[ "${LOG_LEVEL:-6}" ]] || emergency "Cannot continue without LOG_LEVEL. "

info "Start Reactor"
info "__invocation: ${__invocation}"
debug "__file: ${__file}"
debug "__dir: ${__dir}"
debug "__base: ${__base}"
debug "OSTYPE: ${OSTYPE}"

debug "arg_d: ${arg_d:-0}"
debug "arg_v: ${arg_v:-0}"
debug "arg_h: ${arg_h:-0}"

if ! [[ ${#POSITIONAL[@]} -gt 0 ]]; then
  help "Help using ${0}"
else
  for command in ${POSITIONAL[@]}; do
    case $command in
      init)
        init_step
        exit 0
        ;;
      up)
        up_step
        exit 0
        ;;
      down)
        down_step
        exit 0
        ;;
      destroy)
        destroy_step
        exit 0
        ;;
      global-status)
        global_status
        exit 0
        ;;
      ssh)
        kex_pod
        exit 0
        ;;
      reload)
        reload_step
        exit 0
        ;;
    esac
  done
fi

# while [[ ${#POSITIONAL[@]} -gt 0 ]]; do
#   key="$1"

#   case $key in
#     -v|--verbose)
#       arg_v=1
#       shift
#       ;;
#     -d|--debug)
#       arg_d=1
#       shift
#       ;;
#     -n|--no-color)
#       arg_n=1
#       shift
#       ;;
#     -h|--help)
#       arg_h=1
#       shift
#       ;;
#     *)
#       POSITIONAL+=("$1") # save it in an array for later
#       shift # past argument
#       ;;
#   esac
# done
