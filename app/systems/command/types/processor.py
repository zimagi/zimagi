from settings.roles import Roles
from .router import RouterCommand
from .action import ActionCommand
from systems.command.mixins import processor


class ProcessorRouterCommand(RouterCommand):

    def get_priority(self):
        return 95


class ProcessorActionCommand(
    processor.ProcessorMixin,
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
