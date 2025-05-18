from django.conf import settings
from utility.text import wrap

from .base import BaseCommand, SubCommandMixin


class RouterCommand(SubCommandMixin, BaseCommand):

    def add_arguments(self):
        super().add_arguments()

        subcommand_help = [
            "{} {}:".format(self.command_color(self.name), self.notice_color("command to execute")),
            "",
        ]
        for subcommand in self.get_subcommands():
            subcommand_help.extend(
                wrap(
                    subcommand.overview + " ",
                    settings.DISPLAY_WIDTH - 25,
                    init_indent="{:2}{}  -  ".format(" ", self.command_color(subcommand.name)),
                    init_style=self.header_color,
                    indent="".ljust(2),
                )
            )
        self.parser.add_argument("subcommand", nargs=1, type=str, help="\n".join(subcommand_help))

    def parse(self):
        self._parse_debug()
        self._parse_display_width()
        self._parse_no_color()

    def exec(self):
        self.print_help()
