from settings.roles import Roles
from .router import RouterCommand
from .action import ActionCommand


class ModuleRouterCommand(RouterCommand):

    def get_priority(self):
        return 70


class ModuleActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.module_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 70
