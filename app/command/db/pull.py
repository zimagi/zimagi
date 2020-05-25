from systems.command.index import Command


class Action(Command('db.pull')):

    def exec(self):
        self.silent_data('db', self.db.save(self.db_packages, encrypted = False))

    def postprocess(self, result):
        self.db.load(result.get_named_data('db'), encrypted = False)
        self.success("Database packages {} successfully pulled".format(",".join(self.db_packages)))
