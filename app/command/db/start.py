from django.conf import settings

from settings.roles import Roles
from settings.config import Config
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
        self.parse_variable('memory', '--memory', str,
            'PostgreSQL database memory size in g(GB)/m(MB)',
            value_label = 'NUM(g|m)',
            default = '250m'
        )

    def exec(self):
        self.manager.start_service(self, 'mcmi-postgres',
            "postgres:12", { 5432: None },
            environment = {
                'POSTGRES_USER': Config.string('MCMI_POSTGRES_USER', 'mcmi'),
                'POSTGRES_PASSWORD': Config.string('MCMI_POSTGRES_PASSWORD', 'mcmi'),
                'POSTGRES_DB': Config.string('MCMI_POSTGRES_DB', 'mcmi')
            },
            volumes = {
                'mcmi-postgres': {
                    'bind': '/var/lib/postgresql',
                    'mode': 'rw'
                }
            },
            memory = self.options.get('memory'),
            wait = 20
        )
        self.success('Successfully started PostgreSQL database service')
