from systems.command.index import Command


class Action(Command('notification.save'))):

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
