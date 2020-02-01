from settings.roles import Roles
from .router import RouterCommand
from .action import ActionCommand


class ScheduleRouterCommand(RouterCommand):

    def get_priority(self):
        return 95


class ScheduleActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.schedule_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 95
