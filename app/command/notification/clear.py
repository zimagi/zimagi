from settings.roles import Roles
from systems.command.action import ActionCommand


class Command(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.notification_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 95

    def exec(self):
        self._notification.clear()
        self.success("Successfully cleared all command notification preferences")
