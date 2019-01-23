#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

CERT_PATH="${1}"
CERT_SUBJECT="${2:-/C=US/ST=DC/L=Washington/O=cenv/CN=localhost}"
CERT_DAYS="${3:-3650}"

cd "$CERT_PATH"
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
