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


class SaveCommand(
    NotificationActionCommand
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
    NotificationActionCommand
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

class ClearCommand(
    NotificationActionCommand
):
    def exec(self):
        self._notification.clear()
        self.success("Successfully cleared all command notification preferences")


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
            ),
            ('save', SaveCommand),
            ('rm', RemoveCommand),
            ('clear', ClearCommand)
        )
