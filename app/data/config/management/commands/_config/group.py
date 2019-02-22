from systems.command import types
from data.config.management.commands._config import _group as group


class GroupCommand(types.ConfigRouterCommand):

    def get_subcommands(self):
        return (
            ('list', group.ListCommand),
            ('add', group.AddCommand),
            ('rm', group.RemoveCommand),
            ('clear', group.ClearCommand)
        )
