#
#=========================================================================================
# <Zimagi> Command
#

function zimagi_description () {
  render "Execute a Zimagi operation within the reactor environment context"
  export PASSTHROUGH="1"
}

function zimagi_command () {
  zimagi_environment

  ZIMAGI_ARGS=(
    "--rm"
    "--interactive"
    "--tty"
    "--network" "host"
    "--volume" "${__zimagi_app_dir}:/usr/local/share/zimagi"
    "--volume" "${__zimagi_package_dir}:/usr/local/share/zimagi-client"
    "--volume" "${__zimagi_data_dir}:/var/local/zimagi"
  )
  while IFS= read -r variable; do
    ZIMAGI_ARGS=("${ZIMAGI_ARGS[@]}" "--env" "$variable")
  done <<< "$(env | grep -o "ZIMAGI_[_A-Z0-9]*")"

  ZIMAGI_ARGS=("${ZIMAGI_ARGS[@]}" "zimagi_client:dev" "${@}")

  docker run "${ZIMAGI_ARGS[@]}"
}
