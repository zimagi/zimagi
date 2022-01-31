#
#=========================================================================================
# File Handling Utilities
#

function check_binary () {
  if ! command -v "$1" > /dev/null; then
    emergency "Install binary: \"$1\""
  fi
}


function download_binary () {
  if ! command -v "$3/$1" > /dev/null; then
    debug "Download binary: \"$1\" from url: \"$2\""
    curl -sLo "/tmp/$1" "$2"
    debug "\"$1\" was downloaded install binary into folder: \"$3\""
    install "/tmp/$1" "$3"
    rm -f "/tmp/$1"
  fi
}


function create_folder () {
  if ! [ -d "$1" ]; then
    debug "Create folder \"$1\""
    mkdir -p "$1"
  fi
}


function remove_folder () {
  if [ -d "$1" ]; then
    debug "Removing folder \"$1\""
    rm -Rf "$1"
  fi
}


function remove_file () {
  if [ -f "$1" ]; then
    debug "Removing file \"$1\""
    rm -f "$1"
  fi
}


function download_git_repo () {
  DEPTH=${4:-1}
  [[ -d "$2" ]] && rm -rf "$2"
  info "Downloading repo \"$1\" into folder \"$2\" ..."
  git clone --quiet --depth=$DEPTH "$1" "$2"
}
