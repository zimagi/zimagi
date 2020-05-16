from settings.roles import Roles
from base.command.router import RouterCommand
from base.command.action import ActionCommand
from systems.command.factory import resource


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
    LogRouterCommand
):
    def get_subcommands(self):
        return resource.ResourceCommandSet(
            LogActionCommand, self.name,
            allow_update = False
        )
