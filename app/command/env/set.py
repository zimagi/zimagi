from systems.command.action import ActionCommand


class SetCommand(ActionCommand):

    def groups_allowed(self):
        return False

    def server_enabled(self):
        return False

    def get_priority(self):
        return 100

    def parse(self):
        self.parse_environment_repo('--repo')
        self.parse_environment_image('--image')
        self.parse_environment_name()

    def exec(self):
        self.set_env(
            self.environment_name,
            self.environment_repo,
            self.environment_image
        )
