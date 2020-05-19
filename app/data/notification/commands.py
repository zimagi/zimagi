from settings.roles import Roles
from base.command.base import command_set
from base.command.router import RouterCommand
from base.command.action import ActionCommand
from systems.command.factory import resource


class NotificationRouterCommand(RouterCommand):

    def get_priority(self):
        return 95


class NotificationActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.notification_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 95


class Command(
    NotificationRouterCommand
):
    def get_subcommands(self):
        return command_set(
            resource.ResourceCommandSet(
                NotificationActionCommand, self.name,
                allow_access = False,
                allow_update = False,
                allow_remove = False
            )
        )
