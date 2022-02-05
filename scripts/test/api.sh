#
# Run API tests
#
echo "Setting Zimagi ${DOCKER_RUNTIME} host"
"${__zimagi_script_dir}"/zimagi host save default host=localhost encryption_key="$ZIMAGI_ADMIN_API_KEY"
"${__zimagi_script_dir}"/zimagi env get

echo "Running Zimagi ${DOCKER_RUNTIME} API tests"
"${__zimagi_script_dir}"/zimagi user list
"${__zimagi_script_dir}"/zimagi test --types=api
