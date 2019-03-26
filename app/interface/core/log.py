from systems.command.factory import resource
from systems.command.types import log


class Command(
    log.LogRouterCommand
):
    def get_subcommands(self):
        parent = log.LogActionCommand
        return (
            ('list', resource.ListCommand(parent, self.name)),
            ('get', resource.GetCommand(parent, self.name))
        )
