from django.conf import settings

from settings.roles import Roles
from systems.command.action import ActionCommand


class Command(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.module_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 70

    def exec(self):
        self._module._ensure(self, True)
