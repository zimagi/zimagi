#!/usr/bin/env bash
# Create a Django admin user

SCRIPT_USAGE="
 Usage: <project-dir>/scripts/create-admin.sh [ -hf ] <username> <password> [ <email-address> ]

   -f | --force  |  Force the recreation of the admin user with the new information 
   -h | --help   |  Display this help message
"

SCRIPT_DIR="$(cd "$(dirname "$([ `readlink "$0"` ] && echo "`readlink "$0"`" || echo "$0")")"; pwd -P)"
cd "$SCRIPT_DIR/../app"

#-------------------------------------------------------------------------------
# Defaults

DEFAULT_ADMIN_EMAIL="admin@example.com"

#-------------------------------------------------------------------------------
# Option / Argument parsing

SCRIPT_ARGS=()
FORCE_CREATE=''

while [[ $# > 0 ]]
do
  key="$1"

  case $key in
    -h|--help)
      echo "$SCRIPT_USAGE"
      exit 0
    ;;
    -f|--force)
      FORCE_CREATE='true'
    ;;
    *)
      # argument
      SCRIPT_ARGS+=("$key")
    ;;
  esac
  shift
done

ADMIN_USERNAME="${SCRIPT_ARGS[0]}"
ADMIN_PASSWORD="${SCRIPT_ARGS[1]}"
ADMIN_EMAIL="${SCRIPT_ARGS[2]}"

if [ -z "$ADMIN_USERNAME" ]
then
  echo "Django administrator username is required as first argument"
  echo "$SCRIPT_USAGE"
  exit 1
fi

if [ -z "$ADMIN_PASSWORD" ]
then
  echo "Django administrator password is required as second argument"
  echo "$SCRIPT_USAGE"
  exit 1
fi

if [ -z "$ADMIN_EMAIL" ]
then
  ADMIN_EMAIL="$DEFAULT_ADMIN_EMAIL"
fi

#-------------------------------------------------------------------------------
# Execution

#create admin user
if [ ! -z "$FORCE_CREATE" ]
then
  echo "> Recreating admin user: $ADMIN_USERNAME ( $ADMIN_EMAIL )"
  echo "from data.user.models import User; User.objects.filter(username='$ADMIN_USERNAME').delete(); User.objects.create_superuser('$ADMIN_USERNAME', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')" | ./ce shell
else
  echo "> Ensuring admin user: $ADMIN_USERNAME ( $ADMIN_EMAIL )"
  echo "from data.user.models import User; User.objects.filter(username='$ADMIN_USERNAME').first() or User.objects.create_superuser('$ADMIN_USERNAME', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')" | ./ce shell
fi
