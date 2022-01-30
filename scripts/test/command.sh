
echo "Running Zimagi ${DOCKER_RUNTIME} command tests"
"${__zimagi_dir}"/zimagi user list
"${__zimagi_dir}"/zimagi test --types=command
