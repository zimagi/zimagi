#
# Run Command Orchestration tests
#
echo "Running Zimagi ${DOCKER_RUNTIME} command tests"
"${__zimagi_script_dir}"/zimagi user list
"${__zimagi_script_dir}"/zimagi test --types=command
