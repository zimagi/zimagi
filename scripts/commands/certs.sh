#
#=========================================================================================
# <Certs> Command
#

function certs_usage () {
    cat <<EOF >&2

Display or generate self signed SSL certificates

Usage:

  reactor certs [flags] [options]

Flags:
${__zimagi_reactor_core_flags}

    --generate            Generate certificates before displaying them

Options:

    --subject <str>       Certificate subject (requires --generate): ${DEFAULT_CERT_SUBJECT}
    --days <int>          Certificate lifespan (requires --generate): ${DEFAULT_CERT_DAYS}

EOF
  exit 1
}
function certs_command () {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --generate)
      GENERATE=1
      ;;
      --days=*)
      DAYS="${1#*=}"
      ;;
      --days)
      DAYS="$2"
      shift
      ;;
      --subject=*)
      SUBJECT="${1#*=}"
      ;;
      --subject)
      SUBJECT="$2"
      shift
      ;;
      -h|--help)
      certs_usage
      ;;
      *)
      if ! [ -z "$1" ]; then
        error "Unknown argument: ${1}"
        certs_usage
      fi
      ;;
    esac
    shift
  done
  GENERATE=${GENERATE:-0}
  SUBJECT="${SUBJECT:-$DEFAULT_CERT_SUBJECT}/CN=*.$(echo "$ZIMAGI_APP_NAME" | tr '_' '-').local"
  DAYS=${DAYS:-$DEFAULT_CERT_DAYS}

  debug "Command: certs"
  debug "> GENERATE: ${GENERATE}"
  debug "> SUBJECT: ${SUBJECT}"
  debug "> DAYS: ${DAYS}"

  if [ $GENERATE -eq 1 ]; then
    generate_certs "$SUBJECT" $DAYS
  fi
  display_certs
}
