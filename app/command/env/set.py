from systems.command.index import Command


class Action(Command('env.set')):

    def exec(self):
        self.set_env(
            self.environment_name,
            self.environment_repo,
            self.environment_image
        )
