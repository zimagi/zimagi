#!/usr/bin/env bash
#
#=========================================================================================
# Initialize Bash session
#

cat > /etc/profile.d/zimagi.sh <<EOF
cd /project

source /project/reactor

export ZIMAGI_HOST_APP_DIR="/project/app"
export ZIMAGI_HOST_DATA_DIR="/project/data"
export ZIMAGI_HOST_LIB_DIR="/project/lib"
export ZIMAGI_HOST_PACKAGE_DIR="/project/package"
EOF
