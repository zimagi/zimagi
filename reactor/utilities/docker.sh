#
#=========================================================================================
# Docker Utilities
#
function docker_runtime_image () {
  if [ -f "${__zimagi_cli_env_file}" ]
  then
    source "${__zimagi_cli_env_file}"
    if [ -z "$ZIMAGI_RUNTIME_IMAGE" ]
    then
      ZIMAGI_RUNTIME_IMAGE="$ZIMAGI_BASE_IMAGE"
    fi
  else
    ZIMAGI_RUNTIME_IMAGE="$ZIMAGI_DEFAULT_RUNTIME_IMAGE"
  fi
  if ! docker inspect "$ZIMAGI_RUNTIME_IMAGE" >/dev/null 2>&1
  then
    rm -f "${__zimagi_cli_env_file}"
    ZIMAGI_RUNTIME_IMAGE="$ZIMAGI_DEFAULT_RUNTIME_IMAGE"
  fi
  export ZIMAGI_RUNTIME_IMAGE
}
