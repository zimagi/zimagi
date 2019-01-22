#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

CERT_SUBJECT="${1:-/C=US/ST=DC/L=Washington/O=cenv/CN=localhost}"
CERT_DAYS="${2:-3650}"

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
CERT_DIR="$SCRIPT_DIR/../certs"
cd "$CERT_DIR"
#-------------------------------------------------------------------------------

echo "> Generating root CA private key and certificate"
openssl req -new -x509 -sha256 -nodes -days "$CERT_DAYS" -newkey rsa:4096 \
    -subj "$CERT_SUBJECT" \
    -keyout "cenv-ca.key" \
    -out "cenv-ca.crt"

echo "> Generating server private key and certificate signing request"
openssl req -new -sha256 -nodes -days "$CERT_DAYS" -newkey rsa:4096 \
    -subj "$CERT_SUBJECT" \
    -keyout "cenv.key" \
    -out "cenv.csr"

echo "> Generating server certificate through root CA"
openssl x509 -req -CAcreateserial \
    -CA "cenv-ca.crt" \
    -CAkey "cenv-ca.key" \
    -in "cenv.csr" \
    -out "cenv.crt"
