from systems.command.factory import resource
from systems.command.types import schedule


class Command(schedule.ScheduleRouterCommand):

    def get_subcommands(self):
        return resource.ResourceCommandSet(
            schedule.ScheduleActionCommand, 'scheduled_task',
            allow_update = False
        )
