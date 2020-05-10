from settings.roles import Roles
from systems.command.factory import resource
from systems.command.types import host
from .router import RouterCommand
from .action import ActionCommand


class HostRouterCommand(RouterCommand):

    def get_priority(self):
        return 100


class HostActionCommand(ActionCommand):

    def groups_allowed(self):
        return False

    def server_enabled(self):
        return False

    def get_priority(self):
        return 100


class Command(host.HostRouterCommand):

    def get_subcommands(self):
        return resource.ResourceCommandSet(
            host.HostActionCommand, self.name,
            name_options = {
                'optional': '--name'
            }
        )
