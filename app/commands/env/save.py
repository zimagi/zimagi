from systems.commands.index import Command


class Save(Command("env.save")):
    def exec(self):
        self.save_env(name=self.environment_name, **self.environment_fields)
