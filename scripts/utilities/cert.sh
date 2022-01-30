#
#=========================================================================================
# Certificate Utilities
#

function display_certs () {
  build_environment

  info "Zimagi Certificate Authority key"
  notice "${ZIMAGI_CA_KEY}"

  info ""
  info "Zimagi Certificate Authority certificate"
  echo "${ZIMAGI_CA_CERT}"

  info ""
  info "Zimagi key"
  echo "${ZIMAGI_KEY}"

  info ""
  info "Zimagi certificate"
  echo "${ZIMAGI_CERT}"
}

function generate_certs () {
  CERT_SUBJECT="$1"
  CERT_DAYS="$2"

  echo "> Generating root CA private key and certificate"
  openssl req -new -x509 -sha256 -nodes -days $CERT_DAYS -newkey rsa:4096 \
    -subj "$CERT_SUBJECT" \
    -keyout "${__zimagi_certs_dir}/zimagi-ca.key" \
    -out "${__zimagi_certs_dir}/zimagi-ca.crt"

  echo "> Generating server private key and certificate signing request"
  openssl req -new -sha256 -nodes -days $CERT_DAYS -newkey rsa:4096 \
    -subj "$CERT_SUBJECT" \
    -keyout "${__zimagi_certs_dir}/zimagi.key" \
    -out "${__zimagi_certs_dir}/zimagi.csr"

  echo "> Generating server certificate through root CA"
  openssl x509 -req -CAcreateserial \
    -CA "${__zimagi_certs_dir}/zimagi-ca.crt" \
    -CAkey "${__zimagi_certs_dir}/zimagi-ca.key" \
    -in "${__zimagi_certs_dir}/zimagi.csr" \
    -out "${__zimagi_certs_dir}/zimagi.crt"
}
