from systems.command.factory import resource
from systems.command.types import host


class Command(host.HostRouterCommand):

    def get_subcommands(self):
        return resource.ResourceCommandSet(
            host.HostActionCommand, self.name,
            name_options = {
                'optional': '--name'
            }
        )
