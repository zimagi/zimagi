from systems.command.factory import resource
from systems.command.types import log


class Command(
    log.LogRouterCommand
):
    def get_subcommands(self):
        return resource.ResourceCommandSet(
            log.LogActionCommand, self.name,
            allow_update = False
        )
