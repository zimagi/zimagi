from settings import Roles
from .router import RouterCommand
from .action import ActionCommand
from systems.command import mixins


class StorageRouterCommand(RouterCommand):

    def get_priority(self):
        return 50


class StorageActionCommand(
    mixins.data.StorageMixin,
    ActionCommand
):
    def groups_allowed(self):
        return [
            Roles.admin, 
            Roles.storage_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 50
