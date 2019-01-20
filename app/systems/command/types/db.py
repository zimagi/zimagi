from settings import Roles
from .router import RouterCommand
from .action import ActionCommand


class DatabaseRouterCommand(RouterCommand):

    def get_priority(self):
        return 10


class DatabaseActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin, 
            Roles.db_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 10
