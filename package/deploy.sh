#!/bin/bash
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR"
#-------------------------------------------------------------------------------

if [ -z "$PKG_PIP_TOKEN" ]
then
    echo "PKG_PIP_TOKEN environment variable must be defined to deploy application"
    exit 1
fi

echo "Creating PyPi configuration"
if [ ! -f ~/.pypirc ]
then
    echo "
[distutils]
index-servers = pypi

[pypi]
username: __token__
password: $PKG_PIP_TOKEN
" > ~/.pypirc
fi
chmod 600 ~/.pypirc

echo "Installing pip build tools"
python3 -m pip install --no-cache-dir --upgrade setuptools wheel twine

echo "Building pip distribution"
python3 setup.py sdist bdist_wheel --universal --owner=root --group=root

echo "Distributing to PyPi repository"
python3 -m twine upload --verbose dist/*
