from systems.command import types
from data.user.management.commands._user import _token as token


class TokenCommand(types.UserRouterCommand):

    def get_subcommands(self):
        return (
            ('get', token.GetCommand),
            ('rotate', token.RotateCommand),
            ('rm', token.RemoveCommand)
        )
