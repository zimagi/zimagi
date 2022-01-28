#
#=========================================================================================
# Docker Utilities
#

function build_image () {
  SKIP_BUILD=${1:-0}

  debug "Function: build_image"
  debug "> SKIP_BUILD: ${SKIP_BUILD}"

  info "Setting up Zimagi package ..."
  cp -f ${__app_dir}/VERSION ${__package_dir}/VERSION

  info "Building Zimagi application image ..."
  find ${__dir} -name *.pyc -exec rm -f {} \;

  if [ -d "${__data_dir}/run" ]; then
    find "${__data_dir}/run" -type f -exec rm -f {} \;
  fi
  if [ $SKIP_BUILD -ne 1 ]; then
    docker build --force-rm --no-cache \
      --file $ZIMAGI_DOCKER_FILE \
      --tag $ZIMAGI_DEFAULT_RUNTIME_IMAGE \
      --build-arg ZIMAGI_CA_KEY \
      --build-arg ZIMAGI_CA_CERT \
      --build-arg ZIMAGI_KEY \
      --build-arg ZIMAGI_CERT \
      --build-arg ZIMAGI_DATA_KEY \
      ${__dir}
  fi
}
