from settings import Roles
from .router import RouterCommand
from .action import ActionCommand
from systems.command import mixins


class NetworkRouterCommand(RouterCommand):

    def get_priority(self):
        return 7


class NetworkActionCommand(
    mixins.data.NetworkMixin,
    ActionCommand
):
    def groups_allowed(self):
        return [
            Roles.admin, 
            Roles.network_admin
        ]

    def server_enabled(self):
        return True
