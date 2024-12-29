#
#=========================================================================================
# Project variables
#

# Set magic variables for directories.
export __zimagi_project_dir="${2}"

export __zimagi_app_dir="${__zimagi_project_dir}/app"
export __zimagi_package_dir="${__zimagi_project_dir}/package"
export __zimagi_env_dir="${__zimagi_project_dir}/env"
export __zimagi_data_dir="${__zimagi_project_dir}/data"
export __zimagi_lib_dir="${__zimagi_project_dir}/lib"
export __zimagi_module_dir="${__zimagi_lib_dir}/modules"

# Default environment configuration
export ZIMAGI_HOST_APP_DIR="${__zimagi_app_dir}"
export ZIMAGI_HOST_DATA_DIR="${__zimagi_data_dir}"
export ZIMAGI_HOST_LIB_DIR="${__zimagi_lib_dir}"
export ZIMAGI_HOST_PACKAGE_DIR="${__zimagi_package_dir}"

export ZIMAGI_STANDARD_PARENT_IMAGE="ubuntu:22.04"
export ZIMAGI_NVIDIA_PARENT_IMAGE="nvidia/cuda:12.3.2-cudnn9-devel-ubuntu22.04"

export DEFAULT_ZIMAGI_SECRET_KEY="20181105"

export DEFAULT_ZIMAGI_BASE_IMAGE="zimagi/zimagi"
export DEFAULT_ZIMAGI_DOCKER_RUNTIME="standard"
export DEFAULT_ZIMAGI_DOCKER_TAG="dev"
export DEFAULT_ZIMAGI_USER_PASSWORD="zimagi"
export DEFAULT_ZIMAGI_DATA_KEY="zimagi"
export DEFAULT_ZIMAGI_ADMIN_API_KEY="zimagi"
export DEFAULT_ZIMAGI_ADMIN_API_TOKEN="999999999"

# Directory creation
mkdir -p "${__zimagi_data_dir}"
mkdir -p "${__zimagi_lib_dir}"
mkdir -p "${__zimagi_module_dir}"
