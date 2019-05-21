from systems.command.factory import resource
from systems.command.types import environment


class Command(environment.EnvironmentRouterCommand):

    def get_subcommands(self):
        return resource.ResourceCommandSet(
            environment.EnvironmentActionCommand, self.name,
            name_options = {
                'optional': '--name'
            }
        )
