from django.conf import settings
from utility.terminal import TerminalMixin

from zimagi.command import client, messages, schema

from .commands.action import ActionCommand
from .commands.help import HelpCommand
from .commands.router import RouterCommand
from .errors import CommandNotFoundError


class CommandIndex(TerminalMixin):

    def __init__(self):
        self.command_client = client.Client(
            protocol=("http" if settings.COMMAND_HOST == "localhost" else "https"),
            host=settings.COMMAND_HOST,
            port=settings.COMMAND_PORT,
            user=settings.API_USER,
            token=settings.API_USER_TOKEN,
            encryption_key=settings.API_USER_KEY,
            init_commands=False,
            message_callback=self.handle_command_messages,
        )

    def find(self, args):
        command = self.command_client.schema

        if args[0] == "help":
            return HelpCommand(self, command)

        for name in args:
            if isinstance(command, (schema.Root, schema.Router)):
                command = command[name]
            else:
                break

        if isinstance(command, schema.Router):
            return RouterCommand(self, command)
        elif isinstance(command, schema.Action):
            return ActionCommand(self, command)
        else:
            raise CommandNotFoundError(f"Command '{command.name} {name}' not found")

    def handle_command_messages(self, message):
        message = messages.Message.get({"package": message.render()})
        message.display(debug=settings.DEBUG, width=settings.DISPLAY_WIDTH)
