
function server_build_args() {
  zimagi_environment

  export DOCKER_BUILD_VARS=(
    "ZIMAGI_PARENT_IMAGE"
    "ZIMAGI_ENVIRONMENT=${__environment}"
    "ZIMAGI_USER_UID=$(id -u)"
  )
}

function client_build_args() {
  zimagi_environment

  export DOCKER_BUILD_VARS=(
    "ZIMAGI_PARENT_IMAGE"
    "ZIMAGI_ENVIRONMENT=${__environment}"
    "ZIMAGI_USER_UID=$(id -u)"
  )
}
