from systems.commands.index import Command


class Init(Command('module.init')):

    def bootstrap_ensure(self):
        return False

    def exec(self):
        self.ensure_resources(
            reinit = True,
            data_types = self.data_types
        )
