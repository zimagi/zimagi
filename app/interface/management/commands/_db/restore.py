from systems.command import types, mixins


class RestoreCommand(
    types.DatabaseActionCommand
):
    def preprocess(self, params):
        params.data['db'] = self.db.save('all', encrypted = True)

    def exec(self):
        self.db.load(self.options.get('db'), encrypted = True)
        self.success('Database successfully transferred')
