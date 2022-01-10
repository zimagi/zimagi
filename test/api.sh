#-------------------------------------------------------------------------------
RUNTIME="${1}"
#-------------------------------------------------------------------------------

echo "Setting Zimagi ${RUNTIME} host"
./zimagi host save default host=localhost encryption_key="$ZIMAGI_TEST_KEY"
./zimagi env get

echo "Running Zimagi ${RUNTIME} API tests"
./zimagi user list
./zimagi test --types=api
