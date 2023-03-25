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
    if [[ "$2" == *.tar.gz ]]; then
      curl -sLo "/tmp/$1.tar.gz" "$2"
      tar -xzf  "/tmp/$1.tar.gz" -C "/tmp"
      mv "/tmp/$4/$1" "/tmp/$1"
      rm -f "/tmp/$1.tar.gz"
      rm -Rf "/tmp/$4"
    else
      curl -sLo "/tmp/$1" "$2"
    fi
    install "/tmp/$1" "$3"
    rm -f "/tmp/$1"
    debug "\"$1\" was downloaded install binary into folder: \"$3\""
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

function exec_git ()
{
   DIRECTORY="$1";
   shift;
   git --git-dir="${DIRECTORY}/.git" --work-tree="${DIRECTORY}" "$@"
}

function download_git_repo () {
  URL="$1"
  DIRECTORY="$2"
  REFERENCE="${3:-main}"

  info "Fetching repository \"$URL\" into folder \"$DIRECTORY\" ..."

  if [ ! -d "$DIRECTORY" ]; then
    git clone --quiet "$URL" "$DIRECTORY"
  fi
  exec_git "$DIRECTORY" fetch origin --tags
  exec_git "$DIRECTORY" checkout "$REFERENCE"
}
