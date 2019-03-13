from systems.command.base import command_list
from systems.command.factory import resource
from systems.command.types import log


class Command(
    log.LogRouterCommand
):
    def get_command_name(self):
        return 'log'

    def get_subcommands(self):
        parent = log.LogActionCommand
        base_name = self.get_command_name()
        return (
            ('list', resource.ListCommand(parent, base_name)),
            ('get', resource.GetCommand(parent, base_name))
        )
