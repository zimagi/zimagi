from django.conf import settings

from settings.config import Config
from systems.command.types import db


class StartCommand(
    db.DatabaseActionCommand
):
    def server_enabled(self):
        return False

    def parse(self):
        self.parse_variable('memory', '--memory', str,
            'PostgreSQL database memory size in g(GB)/m(MB)',
            value_label = 'NUM(g|m)',
            default = '250m'
        )

    def exec(self):
        self.manager.start_service(self, 'cenv-postgres',
            "postgres:11", { 5432: None },
            environment = {
                'POSTGRES_USER': Config.string('CENV_POSTGRES_USER', 'cenv'),
                'POSTGRES_PASSWORD': Config.string('CENV_POSTGRES_PASSWORD', 'cenv'),
                'POSTGRES_DB': Config.string('CENV_POSTGRES_DB', 'cenv')
            },
            volumes = {
                'cenv-postgres': {
                    'bind': '/var/lib/postgresql',
                    'mode': 'rw'
                }
            },
            memory = self.options.get('memory'),
            wait = 20
        )
        self.success('Successfully started PostgreSQL database service')


class StopCommand(
    db.DatabaseActionCommand
):
    def server_enabled(self):
        return False

    def parse(self):
        self.parse_flag('remove', '--remove', 'remove container and service info after stopping')

    def exec(self):
        self.log_result = False
        self.manager.stop_service(self, 'cenv-postgres', self.options.get('remove'))
        self.success('Successfully stopped PostgreSQL database service')


class PullCommand(
    db.DatabaseActionCommand
):
    def parse(self):
        self.parse_db_packages()

    def interpolate_options(self):
        return False

    def exec(self):
        self.silent_data('db', self.db.save(self.db_packages, encrypted = False))

    def postprocess(self, result):
        self.db.load(result.get_named_data('db'), encrypted = False)
        self.success("Database packages {} successfully pulled".format(",".join(self.db_packages)))


class PushCommand(
    db.DatabaseActionCommand
):
    def parse(self):
        self.parse_db_packages()

    def interpolate_options(self):
        return False

    def preprocess(self, params):
        params.data['db'] = self.db.save(self.db_packages, encrypted = False)

    def exec(self):
        self.db.load(self.options.get('db'), encrypted = False)
        self.success("Database packages {} successfully pushed".format(",".join(self.db_packages)))


class Command(db.DatabaseRouterCommand):

    def get_subcommands(self):
        return (
            ('start', StartCommand),
            ('stop', StopCommand),
            ('pull', PullCommand),
            ('push', PushCommand)
        )
