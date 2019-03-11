from settings.roles import Roles
from .router import RouterCommand
from .action import ActionCommand


class ProjectRouterCommand(RouterCommand):

    def get_priority(self):
        return 70


class ProjectActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.project_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 70
