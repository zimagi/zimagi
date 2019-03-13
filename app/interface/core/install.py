from django.conf import settings

from systems.command.types import project


class Command(
    project.ProjectActionCommand
):
    def get_command_name(self):
        return 'install'

    def get_priority(self):
        return -100

    def exec(self):
        settings.LOADER.install_requirements()
        self.success("Successfully installed project requirements")
