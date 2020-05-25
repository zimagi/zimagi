from systems.command.index import Command


class Action(Command('db.push')):

    def preprocess(self, params):
        params.data['db'] = self.db.save(self.db_packages, encrypted = False)

    def exec(self):
        self.db.load(self.options.get('db'), encrypted = False)
        self.success("Database packages {} successfully pushed".format(",".join(self.db_packages)))
