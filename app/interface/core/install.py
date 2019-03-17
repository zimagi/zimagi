from django.conf import settings

from systems.command.types import module
from utility import docker


class Command(
    module.ModuleActionCommand
):
    def get_command_name(self):
        return 'install'

    def get_priority(self):
        return -100

    def parse(self):
        self.parse_flag('server', '--server', 'install module requirements on server runtime')

    def exec(self):
        settings.LOADER.install_requirements()

        if not self.options.get('server', False):
            env = self.get_env()
            cid = docker.Docker.container_id
            image = docker.Docker.generate_image(env.base_image)

            docker.Docker.create_image(cid, image)
            env.runtime_image = image
            env.save()

        self.success("Successfully installed module requirements")
