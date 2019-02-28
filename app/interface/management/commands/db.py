from systems.command import types


class PullCommand(
    types.DatabaseActionCommand
):
    def exec(self):
        self.silent_data('db', self.db.save('all', encrypted = False))
    
    def postprocess(self, result):
        self.db.load(result.get_named_data('db'), encrypted = False)
        self.success('Database successfully pulled')


class PushCommand(
    types.DatabaseActionCommand
):
    def preprocess(self, params):
        params.data['db'] = self.db.save('all', encrypted = False)

    def exec(self):
        self.db.load(self.options.get('db'), encrypted = False)
        self.success('Database successfully pushed')


class Command(types.DatabaseRouterCommand):

    def get_command_name(self):
        return 'db'

    def get_subcommands(self):
        return (
            ('pull', PullCommand),
            ('push', PushCommand)
        )
