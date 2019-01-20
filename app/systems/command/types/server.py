from settings import Roles
from .router import RouterCommand
from .action import ActionCommand


class ServerRouterCommand(RouterCommand):

    def get_priority(self):
        return 5


class ServerActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin, 
            Roles.server_admin
        ]

    def server_enabled(self):
        return True
