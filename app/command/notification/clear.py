from systems.command.index import Command


class Action(Command('notification.clear')):

    def exec(self):
        self._notification.clear()
        self.success("Successfully cleared all command notification preferences")
