from systems.command import types
from data.user.management.commands import _user as user


class Command(types.UserRouterCommand):

    def get_command_name(self):
        return 'user'

    def get_subcommands(self):
        return (
            ('list', user.ListCommand),
            ('add', user.AddCommand),
            ('update', user.UpdateCommand),
            ('rm', user.RemoveCommand),
            ('group', user.GroupCommand),
            ('token', user.TokenCommand),
        )
