from systems.command import types
from . import _db as db


class Command(types.DatabaseRouterCommand):

    def get_command_name(self):
        return 'db'

    def get_subcommands(self):
        return (
            ('load', db.LoadCommand),
            ('restore', db.RestoreCommand),
            ('save', db.SaveCommand)
        )
