from django.conf import settings

from settings.roles import Roles
from systems.command.action import ActionCommand

import os


class StopCommand(ActionCommand):

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
        def stop_service(name):
            self.manager.stop_service(self, name, self.options.get('remove'))
            self.success("Successfully stopped {} service".format(name))

        self.run_list([
            'mcmi-scheduler',
            'mcmi-worker'
        ], stop_service)
