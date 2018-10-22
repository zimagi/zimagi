#!/usr/bin/env bash
# Create symbolic links in the users bin directory for all python and shell scripts

set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

LOCAL_BIN_DIR=/usr/local/bin

#-------------------------------------------------------------------------------

function create_link() {
  filename="$1"
  
  if [[ $filename =~ ^scripts\/([a-z\-]+)\.(py|sh)$ ]]
  then
    link_name="${BASH_REMATCH[1]}"
    sudo ln -fs "`pwd`/$filename" "$LOCAL_BIN_DIR/$link_name"
  fi
}


for filename in scripts/*.py
do
  if [ "$filename" != "scripts/shared.py" ]
  then
    create_link "$filename"
  fi  
done

for filename in scripts/*.sh
do
  if [ "$filename" != "scripts/vagrant-bash.sh" ]
  then
    create_link "$filename"
  fi  
done