from settings.roles import Roles
from base.command.base import command_set
from base.command.router import RouterCommand
from base.command.action import ActionCommand
from systems.command.factory import resource



class GroupRouterCommand(RouterCommand):

    def get_priority(self):
        return 80


class GroupActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.user_admin,
            Roles.config_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 80


class Command(GroupRouterCommand):

    def get_subcommands(self):
        return command_set(
            resource.ResourceCommandSet(
                GroupActionCommand, self.name,
                provider_name = self.name
            )
        )
