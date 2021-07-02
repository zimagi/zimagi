#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

CERT_PATH="${1}"
CERT_REPO="${2:-https://github.com/zimagi/certificates.git}"
CERT_REFERENCE="${3:-main}"
#-------------------------------------------------------------------------------

echo "> Fetching Zimagi development SSL certificates"
rm -Rf "$CERT_PATH"
git clone --branch="$CERT_REFERENCE" "$CERT_REPO" "$CERT_PATH"
