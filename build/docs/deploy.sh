#!/usr/bin/env bash
#
# Update the GitHub pages documentation site
#
# >> This script must be run within a Python environment
#
set -e

SCRIPT_USAGE="
 Usage: deploy.sh [ -h ] <git-remote> [ <source-branch> ]

   -m | --message  |  Override the documentation update commit message
   -h | --help     |  Display this help message
"

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

#-------------------------------------------------------------------------------
# Defaults

DEFAULT_SOURCE_BRANCH="`git branch | grep '*' | sed -r -e 's/^\*[[:space:]]+//'`"
GH_PAGES_BRANCH="gh-pages"
GH_PAGES_REMOTE=""

DOC_UPDATE_MESSAGE="Building and publishing documentation updates"

BUILD_DIR="/tmp/mcmi-gh-pages"
SITE_TEMP_DIR="/tmp/mcmi-html-docs"

#-------------------------------------------------------------------------------
# Option / Argument parsing

SCRIPT_ARGS=()

while [[ $# > 0 ]]
do
  key="$1"

  case $key in
    -h|--help)
      echo "$SCRIPT_USAGE"
      exit 0
    ;;
    -u|--update)
      DOC_UPDATE_MESSAGE="$2"
      shift
    ;;
    *)
      # argument
      SCRIPT_ARGS+=("$key")
    ;;
  esac
  shift
done

GH_PAGES_REMOTE="${SCRIPT_ARGS[0]}"

if [ -z "$GH_PAGES_REMOTE" ]
then
  echo "GitHub pages remote required for deployment"
  exit 1
fi

SOURCE_BRANCH="${SCRIPT_ARGS[1]}"

if [ -z "$SOURCE_BRANCH" ]
then
  SOURCE_BRANCH="$DEFAULT_SOURCE_BRANCH"
fi

#-------------------------------------------------------------------------------
# Execution

# IMPORTANT: This script should be NON-destructive of the current repository
# in case there is unstaged work or untracked files we don't want to wipe
# accidentally!!!!  This means we need to pull a fresh version to work with.

if which git >/dev/null && which make >/dev/null
then
    # Ensure a clean build
    rm -Rf "$BUILD_DIR"
    rm -Rf "$SITE_TEMP_DIR"

    # Fetch source repository
    git clone -b "$SOURCE_BRANCH" "$GH_PAGES_REMOTE" "$BUILD_DIR"
    cd "$BUILD_DIR/docs"

    # Build and preserve documentation
    make html
    mv _build/html "$SITE_TEMP_DIR"

    # Replace all files with generated documentation site
    cd "$BUILD_DIR"
    git checkout "$GH_PAGES_BRANCH"

    if [ -f CNAME ]
    then
      mv CNAME /tmp
    fi

    rm -Rf *
    rm -Rf .circleci
    mv $SITE_TEMP_DIR/* ./

    if [ -f /tmp/CNAME ]
    then
      mv /tmp/CNAME CNAME
    fi

    mkdir .circleci
    cat > .circleci/config.yml <<END
version: 2
jobs:
  build:
    branches:
      ignore: $GH_PAGES_BRANCH
END

    # Disable GitHub Jekyll
    touch .nojekyll

    # Update Git repository and publish site updates
    git add -A
    git diff-index --quiet HEAD || git commit -m "$DOC_UPDATE_MESSAGE"
    git push origin "$GH_PAGES_BRANCH"

    # Clean up after ourselves
    rm -Rf "$SITE_TEMP_DIR"
    rm -Rf "$BUILD_DIR"

else
    echo "The deploy script requires git and make to be installed"
    exit 1
fi