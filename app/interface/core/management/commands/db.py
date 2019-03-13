from systems.command.base import command_list
from systems.command.types import db


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
            ('pull', PullCommand),
            ('push', PushCommand)
        )
