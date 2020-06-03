#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

CERT_PATH="${1}"
CERT_SUBJECT="${2:-/C=US/ST=DC/L=Washington/O=zimagi/CN=localhost}"
CERT_DAYS="${3:-3650}"

mkdir -p "$CERT_PATH"
cd "$CERT_PATH"
#-------------------------------------------------------------------------------

echo "> Generating root CA private key and certificate"
openssl req -new -x509 -sha256 -nodes -days "$CERT_DAYS" -newkey rsa:4096 \
    -subj "$CERT_SUBJECT" \
    -keyout "zimagi-ca.key" \
    -out "zimagi-ca.crt"

echo "> Generating server private key and certificate signing request"
openssl req -new -sha256 -nodes -days "$CERT_DAYS" -newkey rsa:4096 \
    -subj "$CERT_SUBJECT" \
    -keyout "zimagi.key" \
    -out "zimagi.csr"

echo "> Generating server certificate through root CA"
openssl x509 -req -CAcreateserial \
    -CA "zimagi-ca.crt" \
    -CAkey "zimagi-ca.key" \
    -in "zimagi.csr" \
    -out "zimagi.crt"
