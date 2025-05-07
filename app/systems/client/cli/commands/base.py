import argparse

from django.conf import settings
from django.core.management.base import CommandParser
from utility.terminal import TerminalMixin
from utility.text import wrap_page

from ..args import CommandArgumentMixin
from ..errors import CommandNotFoundError


class SubCommandMixin:

    def __init__(self, index, schema):
        super().__init__(index, schema)
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

    def __init__(self, index, schema):
        self.index = index
        self.client = index.command_client
        self.schema = schema

    def get_arg_boundary(self):
        return 1

    def run_from_argv(self, argv):
        self.args = argv[self.get_arg_boundary() :]
        self.exec()

    def exec(self):
        raise NotImplementedError("Method 'exec' must be implemented in subclasses of BaseExecutable")


class BaseCommand(CommandArgumentMixin, BaseExecutable):

    def __init__(self, index, schema):
        super().__init__(index, schema)

        self.name = schema.name
        self.overview = schema.overview
        self.description = schema.description
        self.epilog = schema.epilog
        self.priority = schema.priority
        self.resource = schema.resource

    def get_arg_boundary(self):
        return len(self.name.split(" ")) + 1

    def run_from_argv(self, argv):
        self._create_parser()

        self.args = argv[self.get_arg_boundary() :]

        if "-h" in self.args or "--help" in self.args:
            return self.print_help()

        self.options = vars(self.parser.parse_args(self.args))
        self.exec()

    def _create_parser(self):
        def display_error(message):
            self.print(self.error_color(f"Error: {message}"))
            self.print_help()
            self.exit(1)

        if not getattr(self, "parser", None):
            epilog = "\n".join(wrap_page(self.epilog)) if self.epilog else ""

            self.parser = CommandParser(
                prog=self.command_color(f"zimagi {self.name}"),
                description="\n".join(
                    wrap_page(self.description, init_indent=" ", init_style=self.header_color, indent="  ")
                ),
                epilog=epilog,
                formatter_class=lambda prog: argparse.RawTextHelpFormatter(
                    prog, indent_increment=2, max_help_position=30, width=settings.DISPLAY_WIDTH
                ),
                called_from_command_line=True,
            )
            self.parser.error = display_error

            self.add_arguments()

    def print_help(self):
        self._create_parser()

        self.print("")
        self.print(self.parser.format_help())

    def add_arguments(self):
        self.parse()

    def parse(self):
        # Override in subclass
        pass

    def _parse_debug(self):
        self.parse_flag(
            "debug",
            "--debug",
            "run in debug mode with error tracebacks",
            default=settings.DEBUG,
        )

    def _parse_display_width(self):
        self.parse_variable(
            "display_width",
            "--display-width",
            int,
            "CLI display width",
            value_label="WIDTH",
            default=settings.DISPLAY_WIDTH,
        )

    def _parse_no_color(self):
        self.parse_flag(
            "no_color",
            "--no-color",
            "don't colorize the command output",
            default=not settings.DISPLAY_COLOR,
        )
