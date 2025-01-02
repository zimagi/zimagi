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
}
