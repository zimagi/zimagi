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
        name_field = 'curr_env_name'
        parent = environment.EnvironmentActionCommand

        return (
            ('list', resource.ListCommand(parent, name)),
            ('get', resource.GetCommand(
                parent, name,
                name_field = name_field
            )),
            ('set', SetCommand),
            ('save', resource.SaveCommand(
                parent, name,
                provider_name = name,
                name_field = name_field
            )),
            ('rm', resource.RemoveCommand(
                parent, name,
                name_field = name_field,
                post_methods = {
                    'delete_env': None
                }
            ))
        )
