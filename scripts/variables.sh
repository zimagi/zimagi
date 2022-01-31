#
#=========================================================================================
# Project variables
#

# Set top level directory as working directory
cd "${__zimagi_dir}"

# Set magic variables for current file, directory, os, etc.
export __zimagi_file="${__zimagi_script_dir}/${__zimagi_base}"
export __zimagi_test_dir="${__zimagi_script_dir}/test"
export __zimagi_binary_dir="${__zimagi_dir}/bin"
export __zimagi_docker_dir="${__zimagi_dir}/docker"
export __zimagi_build_dir="${__zimagi_dir}/build"
export __zimagi_charts_dir="${__zimagi_dir}/charts"
export __zimagi_certs_dir="${__zimagi_dir}/certs"

export __zimagi_app_dir="${__zimagi_dir}/app"
export __zimagi_package_dir="${__zimagi_dir}/package"
export __zimagi_data_dir="${__zimagi_dir}/data"
export __zimagi_lib_dir="${__zimagi_dir}/lib"

export __zimagi_app_env_file="${__zimagi_data_dir}/app.env"
export __zimagi_runtime_env_file="${__zimagi_data_dir}/runtime.env"
export __zimagi_cli_env_file="${__zimagi_data_dir}/cli.env"

# shellcheck disable=SC2034,SC2015
export __zimagi_reactor_invocation="$(printf %q "${__zimagi_file}")$( (($#)) && printf ' %q' "$@" || true)"
export __zimagi_reactor_core_flags="
    -v --verbose                      Enable verbose mode, print script as it is executed
    -d --debug                        Enables debug mode
    -n --no-color                     Disable color output
    -h --help                         Display help message"

# Default environment configuration
export LOG_LEVEL="${LOG_LEVEL:-6}" # 7 = debug -> 0 = emergency
export NO_COLOR="${NO_COLOR:-}"    # true = disable color. otherwise autodetected

export DEFAULT_APP_NAME="zimagi"
export DEFAULT_DOCKER_RUNTIME="standard"
export DEFAULT_DOCKER_TAG="dev"
export DEFAULT_DATA_KEY="b12e75f78n876543210H36j250162731"
export DEFAULT_TEST_KEY="RFJwNYpqA4zihE8jVkivppZfGVDPnzcq"
export DEFAULT_TEST_SCRIPT_NAME="command"
export DEFAULT_CERT_SUBJECT="/C=US/ST=DC/L=Washington/O=zimagi/CN=localhost"
export DEFAULT_CERT_DAYS=3650
