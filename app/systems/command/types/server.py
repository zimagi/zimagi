from .router import RouterCommand
from .action import ActionCommand


class ServerRouterCommand(RouterCommand):

    def get_priority(self):
        return 5


class ServerActionCommand(ActionCommand):

    def server_enabled(self):
        return True
