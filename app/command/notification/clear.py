from systems.command.index import Command


class Clear(Command('notification.clear')):

    def exec(self):
        self._notification.clear()
        self.success("Successfully cleared all command notification preferences")
