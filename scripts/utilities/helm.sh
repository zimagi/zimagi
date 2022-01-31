#
#=========================================================================================
# Helm Utilities
#

function install_helm () {
  if ! command -v "${__zimagi_binary_dir}/helm" > /dev/null; then
    info "Installing Helm ..."

    info "Downloading Helm installer ..."
    curl -o /tmp/helm_install.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get 2>/dev/null
    chmod 700 /tmp/helm_install.sh

    info "Running Helm installer ..."
    export HELM_INSTALL_DIR="${__zimagi_binary_dir}"
    /tmp/helm_install.sh -v "v${HELM_VERSION}" --no-sudo >/dev/null 2>&1
    rm -f /tmp/helm_install.sh
  fi
}

function add_helm_repository () {
  "${__zimagi_binary_dir}"/helm repo add "$1" "$2"
}
