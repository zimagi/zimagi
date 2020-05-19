from django.conf import settings

from settings.roles import Roles
from systems.command.action import ActionCommand
from systems.command.mixins.command.db import DatabaseMixin


class Command(
    DatabaseMixin,
    ActionCommand
):
    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.db_admin,
            Roles.processor_admin
        ]

    def get_priority(self):
        return 95

    def server_enabled(self):
        return False

    def parse(self):
        self.parse_flag('remove', '--remove', 'remove container and service info after stopping')

    def exec(self):
        self.log_result = False
        self.manager.stop_service(self, 'mcmi-postgres', self.options.get('remove'))
        self.success('Successfully stopped PostgreSQL database service')
