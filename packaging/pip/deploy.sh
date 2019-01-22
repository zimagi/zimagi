#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR"
#-------------------------------------------------------------------------------

sudo pip3 install --no-cache-dir --upgrade setuptools wheel twine
sudo python3 setup.py sdist bdist_wheel --owner=root --group=root
sudo python3 -m twine upload dist/*

sudo rm -Rf build
sudo rm -Rf cenv.egg-info
sudo rm -Rf dist