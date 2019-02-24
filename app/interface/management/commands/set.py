from systems.command import types, mixins


class Command(types.EnvironmentActionCommand):

    def get_command_name(self):
        return 'set'

    def parse(self):
        self.parse_env_repo('--repo')
        self.parse_env_image('--image')
        self.parse_env_name()

    def exec(self):
        self.set_env(self.env_name, self.env_repo, self.env_image)
