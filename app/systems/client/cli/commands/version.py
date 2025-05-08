from django.conf import settings

from zimagi.command.messages import TableMessage

from .action import ActionCommand


class VersionCommand(ActionCommand):

    def exec(self):
        TableMessage([["Client version", settings.VERSION]]).display()
        self.client.execute(self.name, **self.options)
        self.print("")

    def handle_message(self, message):
        if not message.system:
            super().handle_message(message)
