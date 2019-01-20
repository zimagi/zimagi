from settings import Roles
from .router import RouterCommand
from .action import ActionCommand


class StorageRouterCommand(RouterCommand):

    def get_priority(self):
        return 2


class StorageActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin, 
            Roles.storage_admin
        ]

    def server_enabled(self):
        return True
