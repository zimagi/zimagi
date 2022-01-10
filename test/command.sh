#-------------------------------------------------------------------------------
RUNTIME="${1}"
#-------------------------------------------------------------------------------

echo "Running Zimagi ${RUNTIME} command tests"
./zimagi user list
./zimagi test --types=command
