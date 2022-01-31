#!/usr/bin/env bash
#
#=========================================================================================
# Initialize Bash session
#

cat > /etc/profile.d/zimagi.sh <<EOF
cd /project

source /project/scripts/reactor path

export ZIMAGI_HOST_APP_DIR="/project/app"
export ZIMAGI_HOST_DATA_DIR="/project/data"
export ZIMAGI_HOST_LIB_DIR="/project/lib"
EOF
