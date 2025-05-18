from systems.commands.index import Command


class Save(Command("notification.save")):
    def exec(self):
        command = self.notify_command
        instance, created = self._notification.store(command)

        for group in self.notify_groups:
            if self.notify_failure:
                instance.failure_groups.get_or_create(group=group)
                self.success(f"Group {group.name} subscribed to {command} failure notifications")
            else:
                instance.groups.get_or_create(group=group)
                self.success(f"Group {group.name} subscribed to {command} notifications")
