#
#=========================================================================================
# Project variables
#

# Set magic variables for current file, directory, os, etc.
export __skaffold_dir="${__dir}/.skaffold"
export __binary_dir="${__skaffold_dir}/bin"
export __docker_dir="${__dir}/docker"
export __build_dir="${__dir}/build"
export __charts_dir="${__dir}/charts"
export __certs_dir="${__dir}/certs"

export __app_dir="${__dir}/app"
export __package_dir="${__dir}/package"
export __data_dir="${__dir}/data"
export __lib_dir="${__dir}/lib"

export __env_file="${__dir}/.env"
export __docker_env_file="${__dir}/.docker"
export __cli_env_file="${__data_dir}/zimagi.env"

# shellcheck disable=SC2034,SC2015
export __invocation="$(printf %q "${__file}")$( (($#)) && printf ' %q' "$@" || true)"
export __core_help_flags="
    -v --verbose                      Enable verbose mode, print script as it is executed
    -d --debug                        Enables debug mode
    -n --no-color                     Disable color output
    -h --help                         Display help message"

# Default environment configuration
export LOG_LEVEL="${LOG_LEVEL:-6}" # 7 = debug -> 0 = emergency
export NO_COLOR="${NO_COLOR:-}"    # true = disable color. otherwise autodetected

export DEFAULT_APP_NAME=zimagi
export DEFAULT_DOCKER_RUNTIME=standard
export DEFAULT_DOCKER_TAG=dev
export DEFAULT_DATA_KEY="0123456789876543210"
