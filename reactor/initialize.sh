#
#=========================================================================================
# Project variables
#

# Set magic variables for directories.
export __zimagi_project_dir="${__docker_dir}/${1}"

export __zimagi_app_dir="${__zimagi_project_dir}/app"
export __zimagi_package_dir="${__zimagi_project_dir}/package"
export __zimagi_data_dir="${__zimagi_project_dir}/data"
export __zimagi_lib_dir="${__zimagi_project_dir}/lib"
export __zimagi_module_dir="${__zimagi_lib_dir}/modules"

# Default environment configuration
if [[ "$PATH" != *"${__zimagi_project_dir}"* ]]; then
  export PATH="${__zimagi_project_dir}:$PATH"
fi

export DEFAULT_ZIMAGI_STANDARD_PARENT_IMAGE="ubuntu:22.04"
export DEFAULT_ZIMAGI_NVIDIA_PARENT_IMAGE="nvidia/cuda:12.3.2-cudnn9-devel-ubuntu22.04"

export DEFAULT_ZIMAGI_CLI_POSTGRES_PORT=5432
export DEFAULT_ZIMAGI_CLI_REDIS_PORT=6379
export DEFAULT_ZIMAGI_CLI_COMMAND_PORT=5123
export DEFAULT_ZIMAGI_CLI_DATA_PORT=5323
export DEFAULT_ZIMAGI_CLI_CELERY_FLOWER_PORT=5555

export DEFAULT_ZIMAGI_KUBERNETES_COMMAND_PORT=5133
export DEFAULT_ZIMAGI_KUBERNETES_DATA_PORT=5333

export DEFAULT_ZIMAGI_SECRET_KEY="XXXXXX20181105"
export DEFAULT_ZIMAGI_POSTGRES_DB="zimagi"
export DEFAULT_ZIMAGI_POSTGRES_USER="postgres"
export DEFAULT_ZIMAGI_POSTGRES_PASSWORD="A1B3C5D7E9F10"
export DEFAULT_ZIMAGI_REDIS_PASSWORD="A1B3C5D7E9F10"

export DEFAULT_ZIMAGI_APP_NAME="zimagi"
export DEFAULT_ZIMAGI_BASE_IMAGE="zimagi/zimagi"
export DEFAULT_ZIMAGI_DOCKER_RUNTIME="standard"
export DEFAULT_ZIMAGI_DOCKER_TAG="dev"
export DEFAULT_ZIMAGI_USER_PASSWORD="en7hs0hb36kq9l1u00cz7v"
export DEFAULT_ZIMAGI_DATA_KEY="b12e75f78n876543210H36j250162731"
export DEFAULT_ZIMAGI_ADMIN_API_KEY="RFJwNYpqA4zihE8jVkivppZfGVDPnzcq"
export DEFAULT_ZIMAGI_ADMIN_API_TOKEN="uy5c8xiahf93j2pl8s00e6nb32h87dn3"

# Directory creation
mkdir -p "${__zimagi_data_dir}"
mkdir -p "${__zimagi_lib_dir}"
mkdir -p "${__zimagi_module_dir}"
