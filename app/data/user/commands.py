from django.conf import settings

from settings.roles import Roles
from base.command.base import command_set
from base.command.router import RouterCommand
from base.command.action import ActionCommand
from systems.command.factory import resource


class UserRouterCommand(RouterCommand):

    def get_priority(self):
        return 85


class UserActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.user_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 85


class Command(UserRouterCommand):

    def get_subcommands(self):
        return command_set(
            resource.ResourceCommandSet(
                UserActionCommand, self.name,
                provider_name = self.name
            )
        )
