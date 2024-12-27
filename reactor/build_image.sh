#!/bin/bash
#-------------------------------------------------------------------------------
set -e

#-------------------------------------------------------------------------------
NO_CACHE=$1
#-------------------------------------------------------------------------------

# Initialie Zimagi environment
zimagi_environment

# Clean directories
cp -f "${__zimagi_app_dir}/VERSION" "${__zimagi_package_dir}/VERSION"

find "${__zimagi_app_dir}" -name *.pyc -exec rm -f {} \;
find "${__zimagi_package_dir}" -name *.pyc -exec rm -f {} \;
find "${__zimagi_lib_dir}" -name *.pyc -exec rm -f {} \;

if [ -d "${__zimagi_data_dir}/run" ]; then
  for service_file in "${__zimagi_data_dir}/run"/*.data; do
    if [[ $NO_CACHE -eq 1 ]] || \
      [[ "$service_file" =~ "command-api" ]] || \
      [[ "$service_file" =~ "data-api" ]] || \
      [[ "$service_file" =~ "scheduler" ]] || \
      [[ "$service_file" =~ "controller" ]] || \
      [[ "$service_file" =~ "worker"* ]]; then
      info "Removing Zimagi files"
      rm -f "$service_file"
    fi
  done
fi

# Build Docker Build Environment
export ZIMAGI_CA_KEY="${APP_CA_KEY}"
export ZIMAGI_CA_CERT="${APP_CA_CERT}"
export ZIMAGI_KEY="${APP_KEY}"
export ZIMAGI_CERT="${APP_CERT}"

export DOCKER_BUILD_VARS=(
  "ZIMAGI_PARENT_IMAGE"
  "ZIMAGI_USER_UID=$(id -u)"
  "ZIMAGI_USER_PASSWORD"
  "ZIMAGI_CA_KEY"
  "ZIMAGI_CA_CERT"
  "ZIMAGI_KEY"
  "ZIMAGI_CERT"
  "ZIMAGI_DATA_KEY"
  "ZIMAGI_DEFAULT_MODULES"
)
