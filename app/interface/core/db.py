from systems.command.base import command_list
from systems.command.types import db
from utility.docker import Docker


class StartCommand(
    db.DatabaseActionCommand
):
    def parse(self):
        self.parse_variable('memory', '--memory', str,
            'PostgreSQL database memory size in g(GB)/m(MB)',
            value_label = 'NUM(g|m)',
            default = '250m'
        )

    def exec(self):
        Docker.start_postgres(self,
            memory = self.options.get('memory')
        )
        self.success('Successfully started PostgreSQL database service')


class StopCommand(
    db.DatabaseActionCommand
):
    def exec(self):
        Docker.stop_postgres(self)
        self.success('Successfully stopped PostgreSQL database service')


class PullCommand(
    db.DatabaseActionCommand
):
    def exec(self):
        self.silent_data('db', self.db.save('all', encrypted = False))

    def postprocess(self, result):
        self.db.load(result.get_named_data('db'), encrypted = False)
        self.success('Database successfully pulled')


class PushCommand(
    db.DatabaseActionCommand
):
    def preprocess(self, params):
        params.data['db'] = self.db.save('all', encrypted = False)

    def exec(self):
        self.db.load(self.options.get('db'), encrypted = False)
        self.success('Database successfully pushed')


class Command(db.DatabaseRouterCommand):

    def get_command_name(self):
        return 'db'

    def get_subcommands(self):
        return (
            ('start', StartCommand),
            ('stop', StopCommand),
            ('pull', PullCommand),
            ('push', PushCommand)
        )
