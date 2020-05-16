from settings.roles import Roles
from base.command.router import RouterCommand
from base.command.action import ActionCommand
from systems.command.factory import resource


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


class Command(HostRouterCommand):

    def get_subcommands(self):
        return resource.ResourceCommandSet(
            HostActionCommand, self.name,
            name_options = {
                'optional': '--name'
            }
        )
