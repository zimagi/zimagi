#!/usr/bin/env bash
#-------------------------------------------------------------------------------
set -e

LOG_FILE="${1:-/dev/stderr}"
SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/.."

CERT_SUBJECT="${1:-/C=US/ST=DC/L=Washington/O=cenv/CN=localhost}"
CERT_DAYS="${2:-3650}"
LOG_FILE="${3:-/dev/stderr}"

#-------------------------------------------------------------------------------

mkdir -p data/certs

echo "> Generating root CA private key and certificate" | tee -a "$LOG_FILE"
openssl req -new -x509 -sha256 -nodes -days "$CERT_DAYS" -newkey rsa:4096 \
    -subj "$CERT_SUBJECT" \
    -keyout data/certs/cenv-ca.key \
    -out data/certs/cenv-ca.crt \
    >>"$LOG_FILE" 2>&1

echo "> Generating server private key and certificate signing request" | tee -a "$LOG_FILE"
openssl req -new -sha256 -nodes -days "$CERT_DAYS" -newkey rsa:4096 \
    -subj "$CERT_SUBJECT" \
    -keyout data/certs/cenv.key \
    -out data/certs/cenv.csr \
    >>"$LOG_FILE" 2>&1

echo "> Generating server certificate through root CA" | tee -a "$LOG_FILE"
openssl x509 -req -CAcreateserial \
    -CA data/certs/cenv-ca.crt \
    -CAkey data/certs/cenv-ca.key \
    -in data/certs/cenv.csr \
    -out data/certs/cenv.crt \
    >>"$LOG_FILE" 2>&1
