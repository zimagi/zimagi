#!/bin/bash
#-------------------------------------------------------------------------------
set -e

#-------------------------------------------------------------------------------
NO_CACHE=$1
#-------------------------------------------------------------------------------

# Initialize Zimagi environment
cert_environment
zimagi_environment

# Build Docker Build Environment
export ZIMAGI_CA_KEY="${APP_CA_KEY:-}"
export ZIMAGI_CA_CERT="${APP_CA_CERT:-}"
export ZIMAGI_KEY="${APP_KEY:-}"
export ZIMAGI_CERT="${APP_CERT:-}"

export DOCKER_BUILD_VARS=(
  "ZIMAGI_PARENT_IMAGE"
  "ZIMAGI_ENVIRONMENT=${__environment}"
  "ZIMAGI_USER_UID=$(id -u)"
  "ZIMAGI_USER_PASSWORD"
  "ZIMAGI_CA_KEY"
  "ZIMAGI_CA_CERT"
  "ZIMAGI_KEY"
  "ZIMAGI_CERT"
  "ZIMAGI_DATA_KEY"
  "ZIMAGI_DEFAULT_MODULES"
)
