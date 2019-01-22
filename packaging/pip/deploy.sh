#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR"
#-------------------------------------------------------------------------------

if [ -z "$PIP_USER" ]
then
    echo "PIP_USER environment variable must be defined to deploy application"
    exit 1
fi
if [ -z "$PIP_PASSWORD" ]
then
    echo "PIP_PASSWORD environment variable must be defined to deploy application"
    exit 1
fi

if [ ! -f ~/.pypirc ]
then
    echo "
[distutils]
index-servers=
    pypi

[pypi]
username: $PIP_USER
password: $PIP_PASSWORD
" > ~/.pypirc
fi

sudo pip3 install --no-cache-dir --upgrade setuptools wheel twine
sudo python3 setup.py sdist bdist_wheel --owner=root --group=root
sudo python3 -m twine upload dist/*

sudo rm -Rf build
sudo rm -Rf cenv.egg-info
sudo rm -Rf dist