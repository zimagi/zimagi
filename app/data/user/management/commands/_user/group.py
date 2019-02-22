from systems.command import types
from data.user.management.commands._user import _group as group


class GroupCommand(types.UserRouterCommand):

    def get_subcommands(self):
        return (
            ('list', group.ListCommand),
            ('add', group.AddCommand),
            ('rm', group.RemoveCommand),
            ('clear', group.ClearCommand)
        )
