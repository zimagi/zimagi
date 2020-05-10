from settings.roles import Roles
from systems.command.factory import resource
from systems.command.types import schedule
from .router import RouterCommand
from .action import ActionCommand


class ScheduleRouterCommand(RouterCommand):

    def get_priority(self):
        return 95


class ScheduleActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.schedule_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 95


class Command(schedule.ScheduleRouterCommand):

    def get_subcommands(self):
        return resource.ResourceCommandSet(
            schedule.ScheduleActionCommand, 'scheduled_task',
            allow_update = False
        )
