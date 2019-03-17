from django.conf import settings

from systems.command.factory import resource
from systems.command.types import environment


class SetCommand(
    environment.EnvironmentActionCommand
):
    def parse(self):
        self.parse_env_repo('--repo')
        self.parse_env_image('--image')
        self.parse_env_name()

    def exec(self):
        self.set_env(self.env_name, self.env_repo, self.env_image)


class Command(
    environment.EnvironmentRouterCommand
):
    def get_command_name(self):
        return 'env'

    def get_subcommands(self):
        parent = environment.EnvironmentActionCommand
        base_name = self.get_command_name()
        name_field = 'curr_env_name'
        return (
            ('list', resource.ListCommand(parent, base_name)),
            ('get', resource.GetCommand(
                parent, base_name,
                name_field = name_field
            )),
            ('set', SetCommand),
            ('save', resource.SaveCommand(
                parent, base_name,
                provider_name = base_name,
                name_field = name_field
            )),
            ('rm', resource.RemoveCommand(
                parent, base_name,
                name_field = name_field,
                post_methods = {
                    'delete_env': None
                }
            ))
        )
