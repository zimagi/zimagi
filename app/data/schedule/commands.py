from settings.roles import Roles
from base.command.router import RouterCommand
from base.command.action import ActionCommand
from systems.command.factory import resource


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


class Command(ScheduleRouterCommand):

    def get_subcommands(self):
        return resource.ResourceCommandSet(
            ScheduleActionCommand, 'scheduled_task',
            allow_update = False
        )
