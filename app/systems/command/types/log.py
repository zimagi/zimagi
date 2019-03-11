from settings.roles import Roles
from .router import RouterCommand
from .action import ActionCommand


class LogRouterCommand(RouterCommand):

    def get_priority(self):
        return 90


class LogActionCommand(
    ActionCommand
):

    def groups_allowed(self):
        return [
            Roles.admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 90
