from settings.roles import Roles
from systems.command.factory import resource
from systems.command.types import log
from .router import RouterCommand
from .action import ActionCommand


class LogRouterCommand(RouterCommand):

    def get_priority(self):
        return 90


class LogActionCommand(
    ActionCommand
):

    def groups_allowed(self):
        return [
            Roles.admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 90


class Command(
    log.LogRouterCommand
):
    def get_subcommands(self):
        return resource.ResourceCommandSet(
            log.LogActionCommand, self.name,
            allow_update = False
        )
