from .router import RouterCommand
from .action import ActionCommand


class EnvironmentRouterCommand(RouterCommand):

    def get_priority(self):
        return 10


class EnvironmentActionCommand(ActionCommand):

    def server_enabled(self):
        return False

    def get_priority(self):
        return 10
