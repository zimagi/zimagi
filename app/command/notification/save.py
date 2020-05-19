from settings.roles import Roles
from systems.command.action import ActionCommand


class Command(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.notification_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 95

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
