from settings.roles import Roles
from .router import RouterCommand
from .action import ActionCommand


class EnvironmentRouterCommand(RouterCommand):

    def get_priority(self):
        return 100


class EnvironmentActionCommand(ActionCommand):

    def groups_allowed(self):
        return False

    def server_enabled(self):
        return False

    def get_priority(self):
        return 100
