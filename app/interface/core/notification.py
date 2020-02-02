from systems.command.factory import resource
from systems.command.base import command_set
from systems.command.types import notification


class SaveCommand(
    notification.NotificationActionCommand
):
    def parse(self):
        self.parse_group_provider_name('--group-provider')
        self.parse_notify_failure()
        self.parse_notify_command(True)
        self.parse_notify_groups(True)

    def exec(self):
        command = self.notify_command
        instance, created = self._notification.store(command)

        for group in self.notify_groups:
            if self.notify_failure:
                instance.failure_groups.get_or_create(group = group)
                self.success("Group {} subscribed to {} failure notifications".format(
                    group.name, command
                ))
            else:
                instance.groups.get_or_create(group = group)
                self.success("Group {} subscribed to {} notifications".format(
                    group.name, command
                ))

class RemoveCommand(
    notification.NotificationActionCommand
):
    def parse(self):
        self.parse_group_provider_name('--group-provider')
        self.parse_notify_failure()
        self.parse_notify_command(True)
        self.parse_notify_groups(True)

    def exec(self):
        command = self.notify_command
        instance, created = self._notification.store(command)

        for group in self.notify_groups:
            if self.notify_failure:
                instance.failure_groups.filter(group = group).delete()
                self.success("Group {} unsubscribed from {} failure notifications".format(
                    group.name, command
                ))
            else:
                instance.groups.filter(group = group).delete()
                self.success("Group {} unsubscribed from {} notifications".format(
                    group.name, command
                ))


class Command(
    notification.NotificationRouterCommand
):
    def get_subcommands(self):
        return command_set(
            resource.ResourceCommandSet(
                notification.NotificationActionCommand, self.name,
                allow_access = False,
                allow_update = False,
                allow_remove = False
            ),
            ('save', SaveCommand),
            ('rm', RemoveCommand)
        )
