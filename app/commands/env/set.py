from systems.commands.index import Command


class Set(Command('env.set')):

    def exec(self):
        self.set_env(
            self.environment_name,
            self.environment_repo,
            self.environment_image
        )
