#
#=========================================================================================
# <Zimagi> Command
#

function zimagi_description () {
  render "Execute a Zimagi operation within the reactor environment context"
  export PASSTHROUGH="1"
}

function zimagi_command () {
  kubernetes_environment
  zimagi_environment

  if [ ! -f "${__zimagi_env_dir}/secret" ]; then
    cp -f "${__zimagi_env_dir}/secret.example" "${__zimagi_env_dir}/secret"
  fi

  ZIMAGI_ARGS=(
    "--rm"
    "--interactive"
    "--tty"
    "--network" "host"
    "--group-add" "${ZIMAGI_DOCKER_GROUP}"
    "--volume" "/var/run/docker.sock:/var/run/docker.sock"
    "--volume" "${__zimagi_app_dir}:/usr/local/share/zimagi"
    "--volume" "${__zimagi_lib_dir}:/usr/local/lib/zimagi"
    "--volume" "${__zimagi_data_dir}:/var/local/zimagi"
    "--env-file" "${__zimagi_env_dir}/public"
    "--env-file" "${__zimagi_env_dir}/secret"
    "--env" "ZIMAGI_CLI_EXEC=True"
  )
  if [ ! -z "${KUBECONFIG:-}" ]; then
    ZIMAGI_ARGS=("${ZIMAGI_ARGS[@]}" "--volume" "${KUBECONFIG}:/home/zimagi/.kube/config")
  fi
  while IFS= read -r variable; do
    ZIMAGI_ARGS=("${ZIMAGI_ARGS[@]}" "--env" "$variable")
  done <<< "$(env | grep -o "KUBERNETES_[_A-Z0-9]*")"

  while IFS= read -r variable; do
    ZIMAGI_ARGS=("${ZIMAGI_ARGS[@]}" "--env" "$variable")
  done <<< "$(env | grep -o "ZIMAGI_[_A-Z0-9]*")"

  if [ "$ZIMAGI_DOCKER_RUNTIME" != "standard" ]; then
    ZIMAGI_ARGS=("${ZIMAGI_ARGS[@]}" "--runtime" "$ZIMAGI_DOCKER_RUNTIME")
  fi

  if [[ ! "${@}" ]]; then
    ZIMAGI_ARGS=("${ZIMAGI_ARGS[@]}" "$ZIMAGI_RUNTIME_IMAGE" "help")
  else
    ZIMAGI_ARGS=("${ZIMAGI_ARGS[@]}" "$ZIMAGI_RUNTIME_IMAGE" "${@}")
  fi
  docker run "${ZIMAGI_ARGS[@]}"
}
