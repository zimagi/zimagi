from utility.terminal import TerminalMixin

from ..errors import CommandNotFoundError


class SubCommandMixin:

    def __init__(self, client, schema):
        super().__init__(client, schema)
        self.commands = schema.commands

    def get_subcommands(self):
        command_index = {}
        subcommands = []

        for name, subcommand in self.commands.items():
            command_index.setdefault(subcommand.priority, [])
            command_index[subcommand.priority].append(subcommand)

        for priority in sorted(command_index.keys()):
            subcommands.extend(command_index[priority])

        return subcommands

    def find(self, command_name):
        if command_name not in self.commands:
            raise CommandNotFoundError(f"Command '{self.schema.name} {command_name}' not found")
        return self.commands[command_name]


class BaseExecutable(TerminalMixin):

    def __init__(self, client, schema):
        self._client = client
        self._schema = schema

    def exec(self, argv):
        raise NotImplementedError("Method 'exec' must be implemented in subclasses of BaseExecutable")


class BaseCommand(BaseExecutable):

    def __init__(self, client, schema):
        super().__init__(client, schema)
        self.name = schema.name
        self.overview = schema.overview
        self.description = schema.description
        self.priority = schema.priority
        self.resource = schema.resource

    def exec(self, argv):
        raise NotImplementedError("Method 'exec' must be implemented in subclasses of BaseCommand")
