from systems.commands.index import Command


class Remove(Command("notification.remove")):
    def exec(self):
        command = self.notify_command
        instance, created = self._notification.store(command)

        for group in self.notify_groups:
            if self.notify_failure:
                instance.failure_groups.filter(group=group).delete()
                self.success(f"Group {group.name} unsubscribed from {command} failure notifications")
            else:
                instance.groups.filter(group=group).delete()
                self.success(f"Group {group.name} unsubscribed from {command} notifications")
