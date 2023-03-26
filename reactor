#!/usr/bin/env bash
#
# Usage:
#
#  reactor [flags] <command> [args] [flags/options]
#
#=========================================================================================
# Initialization
#
# Environment

SCRIPT_PATH="${BASH_SOURCE[0]}" # bash
if [[ -z "$SCRIPT_PATH" ]]; then
  SCRIPT_PATH="${(%):-%N}" # zsh
fi

((return 0 2>/dev/null) || [[ $ZSH_EVAL_CONTEXT =~ :file$ ]]) && SOURCED=1 || SOURCED=0

export __zimagi_dir="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
export __zimagi_base="$(basename ${SCRIPT_PATH})"
export __zimagi_script_dir="${__zimagi_dir}/scripts"
export __zimagi_data_dir="${__zimagi_dir}/data"

if [[ $SOURCED -eq 1 ]]; then
  # script is being sourced
  if [ -f "${__zimagi_data_dir}/runtime.env.sh" ]; then
    source "${__zimagi_data_dir}/runtime.env.sh"
  fi
  if [ -f "${__zimagi_data_dir}/app.env.sh" ]; then
    source "${__zimagi_data_dir}/app.env.sh"
  fi
  if [[ "$PATH" != *"${__zimagi_dir}"* ]]; then
    export PATH="${__zimagi_dir}:${__zimagi_script_dir}:${__zimagi_dir}/bin:$PATH"
  fi
  return
fi

source "${__zimagi_script_dir}/variables.sh"

for file in "${__zimagi_script_dir}/utilities"/*.sh; do
  source "$file"
done
for file in "${__zimagi_script_dir}/commands"/*.sh; do
  source "$file"
done

import_environment

# Parameter parsing
function usage () {
  cat <<EOF >&2

  Reactor manages the Zimagi local development environment.

  Usage:

    reactor [flags] [command] [flags/options]

  Flags:
${__zimagi_reactor_core_flags}

  Commands:

    help                              Display help information for a command
    init                              Initialize development environment
    up                                Start development environment
    update                            Update the application stack in the development environment
    logs                              Display log entries for Zimagi services
    dashboard                         Launch the Kubernetes Dashboard for Minikube cluster
    shell                             Open a terminal session into a running Zimagi service
    down                              Stop development environment
    destroy                           Purge development environment
    clean                             Clean project resources
    certs                             Display or generate SSL certificates and keys
    test                              Run a suite of Zimagi tests

  Use "reactor <command> --help" for more information about a given command.

  For easier execution in new bash sessions run:

  > source ${__zimagi_dir}/reactor  # exposes zimagi and reactor command aliases

EOF
  exit 1
}


COMMAND_ARGS=()
arg_processed=0
[[ $# -eq 0 ]] && arg_h=1

while [[ $# -gt 0 ]]; do
  case "$1" in
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
      if [ $arg_processed -ne 1 ]; then
        arg_h=1
      else
        COMMAND_ARGS+=("$1")
      fi
      shift
      ;;
    *)
      COMMAND_ARGS+=("$1")
      arg_processed=1
      shift
      ;;
  esac
done

#
#=========================================================================================
# Execution
#

# Error handling
set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

# Log check
[[ "${LOG_LEVEL:-6}" ]] || emergency "Cannot continue without LOG_LEVEL"

# Debug mode
if [[ "${arg_d:-0}" = "1" ]]; then
  #set -o xtrace
  PS4='+(${BASH_SOURCE}:${LINENO}): ${FUNCNAME[0]:+${FUNCNAME[0]}(): }'
  LOG_LEVEL="7"
  # Enable error backtracing
  trap '__err_report "${FUNCNAME:-.}" ${LINENO}' ERR
fi

# Verbose mode
if [[ "${arg_v:-0}" = "1" ]]; then
  set -o verbose
fi

# No color mode
if [[ "${arg_n:-0}" = "1" ]]; then
  NO_COLOR="true"
fi


debug "Top level flags"
debug "> Debug: ${arg_d:-0}"
debug "> Verbosity: ${arg_v:-0}"
debug "> Help: ${arg_h:-0}"

debug "Script properties"
debug "> OS type: ${OSTYPE}"
debug "> OS name: ${__os}"
debug "> CPU arch: ${__architecture}"
debug "> Invocation: ${__zimagi_reactor_invocation}"
debug "> Directory: ${__zimagi_dir}"
debug "> Script directory: ${__zimagi_script_dir}"
debug "> Script file: ${__zimagi_file}"
debug "> Script name: ${__zimagi_base}"

debug "Project and development properties"
debug "> Executable directory: ${__zimagi_binary_dir}"
debug "> Docker directory: ${__zimagi_docker_dir}"
debug "> Helm chart directory: ${__zimagi_charts_dir}"
debug "> Certificate directory: ${__zimagi_certs_dir}"

debug "Zimagi project properties"
debug "> Application directory: ${__zimagi_app_dir}"
debug "> Package directory: ${__zimagi_package_dir}"
debug "> Data directory: ${__zimagi_data_dir}"
debug "> Lib directory: ${__zimagi_lib_dir}"
debug "> Application environment file: ${__zimagi_app_env_file}"
debug "> Runtime environment file: ${__zimagi_runtime_env_file}"
debug "> CLI environment file: ${__zimagi_cli_env_file}"


if [[ "${arg_h:-0}" = "1" ]] || [[ ${#COMMAND_ARGS[@]} -eq 0 ]]; then
  usage
else
  COMMAND="${COMMAND_ARGS[0]}"
  COMMAND_ARGS=("${COMMAND_ARGS[@]:1}")

  case $COMMAND in
    init)
      init_command "${COMMAND_ARGS[@]:-}"
      ;;
    up)
      up_command "${COMMAND_ARGS[@]:-}"
      ;;
    update)
      update_command "${COMMAND_ARGS[@]:-}"
      ;;
    logs)
      logs_command "${COMMAND_ARGS[@]:-}"
      ;;
    dashboard)
      dashboard_command "${COMMAND_ARGS[@]:-}"
      ;;
    shell)
      shell_command "${COMMAND_ARGS[@]:-}"
      ;;
    down)
      down_command "${COMMAND_ARGS[@]:-}"
      ;;
    destroy)
      destroy_command "${COMMAND_ARGS[@]:-}"
      ;;
    clean)
      clean_command "${COMMAND_ARGS[@]:-}"
      ;;
    certs)
      certs_command "${COMMAND_ARGS[@]:-}"
      ;;
    test)
      test_command "${COMMAND_ARGS[@]:-}"
      ;;
    help)
      if ! [[ ${#COMMAND_ARGS[@]} -gt 0 ]]; then
        usage
      else
        "${COMMAND_ARGS[0]}_command" --help
      fi
      ;;
    *)
      error "Unknown command: ${COMMAND}"
      usage
      ;;
  esac
fi
