from systems.command.factory import resource
from systems.command.base import command_set
from systems.command.types import notification


class Command(notification.NotificationRouterCommand):

    def get_subcommands(self):
        return command_set(
            resource.ResourceCommandSet(
                notification.NotificationActionCommand, self.name,
                allow_update = False
            )
        )
