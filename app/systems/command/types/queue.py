from settings.roles import Roles
from .router import RouterCommand
from .action import ActionCommand
from systems.command.mixins import queue


class QueueRouterCommand(RouterCommand):

    def get_priority(self):
        return 95


class QueueActionCommand(
    queue.QueueMixin,
    ActionCommand
):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.processor_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 95
