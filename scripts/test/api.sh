
echo "Setting Zimagi ${DOCKER_RUNTIME} host"
"${__zimagi_dir}"/zimagi host save default host=localhost encryption_key="$ZIMAGI_TEST_KEY"
"${__zimagi_dir}"/zimagi env get

echo "Running Zimagi ${DOCKER_RUNTIME} API tests"
"${__zimagi_dir}"/zimagi user list
"${__zimagi_dir}"/zimagi test --types=api
