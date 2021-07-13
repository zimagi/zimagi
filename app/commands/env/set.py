from systems.commands.index import Command


class Set(Command('env.set')):

    def exec(self):
        self.set_env(
            name = self.environment_name,
            **self.environment_fields
        )
