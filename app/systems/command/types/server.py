from settings import Roles
from .router import RouterCommand
from .action import ActionCommand
from systems.command import mixins


class ServerRouterCommand(RouterCommand):

    def get_priority(self):
        return 35


class ServerActionCommand(
    mixins.data.ServerMixin,
    ActionCommand
):
    def groups_allowed(self):
        return [
            Roles.admin, 
            Roles.server_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 40
