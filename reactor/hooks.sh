#
#=========================================================================================
# Project Hooks
#

function hook_modified () {
  for file in "${__zimagi_module_dir}"/*/*; do
    check_git_status "zimagi module" "$(basename "$file")" "$file"
  done
}

function hook_update () {
  info "Initializing Zimagi CLI ..."
  run_subcommand zimagi env get
  run_subcommand zimagi host save "${__environment}" \
    host="cmd.${ZIMAGI_DOMAIN}" \
    command_port="443" \
    user="${ZIMAGI_ADMIN_USER}" \
    token="${ZIMAGI_DEFAULT_ADMIN_TOKEN}" \
    encryption_key="${ZIMAGI_ADMIN_API_KEY}"
}

function hook_update_host () {
  info "Setting Zimagi CLI default host ${__environment} ..."
  run_subcommand zimagi config save option_environment_host "${__environment}" --local
}
