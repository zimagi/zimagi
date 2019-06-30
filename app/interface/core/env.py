from systems.command.base import command_set
from systems.command.factory import resource
from systems.command.types import environment


class SetCommand(
    environment.EnvironmentActionCommand
):
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


class Command(
    environment.EnvironmentRouterCommand
):
    def get_subcommands(self):
        name = 'environment'
        return command_set(
            resource.ResourceCommandSet(
                environment.EnvironmentActionCommand, name,
                provider_name = name,
                name_field = 'curr_env_name',
                rm_post_methods = {
                    'delete_env': None
                },
                allow_list = False,
                allow_clear = False
            ),
            ('set', SetCommand)
        )
