from settings.roles import Roles
from .router import RouterCommand
from .action import ActionCommand


class NotificationRouterCommand(RouterCommand):

    def get_priority(self):
        return 95


class NotificationActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.notification_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 95
