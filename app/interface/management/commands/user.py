from systems.command.base import command_list
from systems.command import types, mixins, factory
from . import _user as user


class Command(types.UserRouterCommand):

    def get_command_name(self):
        return 'user'

    def get_subcommands(self):
        return command_list(
            factory.ResourceCommands(
                types.UserActionCommand, 'user',
                list_fields = (
                    ('name', 'Username'),
                    ('first_name', 'First name'),
                    ('last_name', 'Last name'),
                    ('email', 'Email'),
                    ('last_login', 'Last login')
                ),
                relations = {
                    'group': 'groups'
                }
            ),
            ('rotate', user.RotateCommand)
        )
