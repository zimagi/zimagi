from django.conf import settings

from settings.roles import Roles
from settings.config import Config
from systems.command.action import ActionCommand


class Command(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.processor_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 95

    def server_enabled(self):
        return False

    def parse(self):
        self.parse_variable('memory', '--memory', str,
            'Redis queue memory size in g(GB)/m(MB)',
            value_label = 'NUM(g|m)',
            default = '250m'
        )

    def exec(self):
        self.manager.start_service(self, 'mcmi-queue',
            "redis:5", { 6379: None },
            docker_command = "redis-server --requirepass {}".format(
                Config.string('MCMI_REDIS_PASSWORD', 'mcmi')
            ),
            volumes = {
                'mcmi-queue': {
                    'bind': '/data',
                    'mode': 'rw'
                }
            },
            memory = self.options.get('memory'),
            wait = 20
        )
        self.set_state('config_ensure', True)
        self.success('Successfully started Redis queue service')
