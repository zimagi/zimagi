from settings import Roles
from .router import RouterCommand
from .action import ActionCommand


class ConfigRouterCommand(RouterCommand):

    def get_priority(self):
        return 75


class ConfigActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin, 
            Roles.config_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 75
