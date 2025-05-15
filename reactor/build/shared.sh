
function server_build_args() {
  zimagi_environment

  export DOCKER_BUILD_VARS=(
    "ZIMAGI_PARENT_IMAGE"
    "ZIMAGI_ENVIRONMENT=${__environment}"
    "ZIMAGI_USER_PASSWORD"
    "ZIMAGI_DEFAULT_MODULES"
  )
}

function client_build_args() {
  zimagi_environment

  export DOCKER_BUILD_VARS=(
    "ZIMAGI_PARENT_IMAGE"
    "ZIMAGI_ENVIRONMENT=${__environment}"
  )
}
