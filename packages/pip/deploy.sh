#!/bin/sh
#-------------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR"
#-------------------------------------------------------------------------------

STATUS=0

echo '1'

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

echo '2'

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

echo '3'

python3 -m pip install --no-cache-dir setuptools wheel twine
python3 setup.py sdist bdist_wheel --owner=root --group=root
python3 -m twine upload dist/*
