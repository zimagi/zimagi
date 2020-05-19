from django.conf import settings

from settings.roles import Roles
from systems.command.action import ActionCommand


class Command(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.processor_admin
        ]

    def get_priority(self):
        return 95

    def server_enabled(self):
        return False

    def parse(self):
        self.parse_flag('remove', '--remove', 'remove container and service info after stopping')

    def exec(self):
        self.manager.stop_service(self, 'mcmi-queue', self.options.get('remove'))
        self.set_state('config_ensure', True)
        self.success('Successfully stopped Redis queue service')
