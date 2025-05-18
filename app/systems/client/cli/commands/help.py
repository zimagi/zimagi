from django.conf import settings
from utility.text import wrap

from zimagi.command.schema import Router

from .base import BaseExecutable, SubCommandMixin
from .router import RouterCommand


class HelpCommand(SubCommandMixin, BaseExecutable):

    def __init__(self, index, schema):
        super().__init__(index, schema)
        self.title = schema.title
        self.description = schema.description

    def get_arg_boundary(self):
        return super().get_arg_boundary() + 1

    def exec(self):
        if not self.args:
            self.render_overview()
        else:
            self.render_command()

    def render_overview(self):
        usage = [
            "",
            "Type '{}' for help on a specific subcommand.".format(
                self.command_color(f"{settings.APP_NAME} help <subcommand> ...")
            ),
            "",
            "Available subcommands:",
            "",
        ]

        def render_command(command, width, init_indent, indent):
            if command.name:
                usage.extend(
                    wrap(
                        f"{self.command_color(command.name)} - {self.header_color(command.overview)}",
                        width,
                        init_indent="".ljust(init_indent),
                        indent="".ljust(indent),
                    )
                )
                if isinstance(command, Router):
                    for subcommand in RouterCommand(self.index, command).get_subcommands():
                        render_command(subcommand, width - 5, init_indent + 5, indent + 5)

        for subcommand in self.get_subcommands():
            if subcommand.name not in ["help", "agent"]:
                render_command(subcommand, settings.DISPLAY_WIDTH, 1, 5)

        self.print("\n".join(usage))

    def render_command(self):
        command = self.index.find(self.args)
        command.print_help()
