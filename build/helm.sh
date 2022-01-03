#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

SCRIPT_USAGE="
 Usage: helm.sh [ -h ] <git-remote> [ <source-branch> ]

   -m | --message  |  Override the documentation update commit message
   -h | --help     |  Display this help message
"

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
HOME_DIR="$SCRIPT_DIR/../.."

VERSION="`cat app/VERSION`"
#-------------------------------------------------------------------------------
# Defaults

DEFAULT_SOURCE_BRANCH="`git branch | grep '*' | sed -r -e 's/^\*[[:space:]]+//'`"
CHART_REMOTE=""

CHART_UPDATE_MESSAGE="Updating Zimagi Helm chart (docker push)"

BUILD_DIR="/tmp/zimagi-chart"

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
      CHART_UPDATE_MESSAGE="$2"
      shift
    ;;
    *)
      # argument
      SCRIPT_ARGS+=("$key")
    ;;
  esac
  shift
done

CHART_REMOTE="${SCRIPT_ARGS[0]}"

if [ -z "$CHART_REMOTE" ]
then
  echo "GitHub remote required for chart update"
  exit 1
fi

SOURCE_BRANCH="${SCRIPT_ARGS[1]}"

if [ -z "$SOURCE_BRANCH" ]
then
  SOURCE_BRANCH="$DEFAULT_SOURCE_BRANCH"
fi

#-------------------------------------------------------------------------------
if which git >/dev/null
then
    git clone -b "$SOURCE_BRANCH" "$CHART_REMOTE" "$BUILD_DIR"
    cd "$BUILD_DIR"

    echo "Installing Python requirements"
    pip install --no-cache-dir -r .circleci/version_updater/requirements.txt

    echo "Updating Zimagi chart version"
    python .circleci/version_updater/version_updater.py -c ./charts/zimagi -t $VERSION

    echo "Pushing chart repository changes"
    git add -A
    git diff-index --quiet HEAD || git commit -m "$CHART_UPDATE_MESSAGE"
    git push origin "$SOURCE_BRANCH"

    # Clean up after ourselves
    rm -Rf "$BUILD_DIR"
else
    echo "The helm update script requires git to be installed"
    exit 1
fi
