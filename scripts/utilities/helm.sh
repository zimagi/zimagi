#
#=========================================================================================
# Helm Utilities
#

function add_helm_repository () {
  if [ -f "${__zimagi_binary_dir}/helm" ]; then
    "${__zimagi_binary_dir}"/helm repo add "$1" "$2"
  fi
}
