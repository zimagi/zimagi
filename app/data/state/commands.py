from settings.roles import Roles
from base.command.router import RouterCommand
from base.command.action import ActionCommand
from systems.command.factory import resource


class StateRouterCommand(RouterCommand):

    def get_priority(self):
        return 95


class StateActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.config_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 95


class Command(StateRouterCommand):

    def get_subcommands(self):
        return resource.ResourceCommandSet(
            StateActionCommand, self.name,
            allow_update = False,
        )
