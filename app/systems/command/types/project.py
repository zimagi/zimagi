from .router import RouterCommand
from .action import ActionCommand


class ProjectRouterCommand(RouterCommand):

    def get_priority(self):
        return 2


class ProjectActionCommand(ActionCommand):

    def server_enabled(self):
        return True
