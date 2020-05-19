
from django.conf import settings
from django.core.management.base import CommandError

from systems.command import base
from utility.text import wrap

import sys
import re


class RouterCommand(base.BaseCommand):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_subcommands()

    def init_subcommands(self):
        self.subcommands = {}

        for info in self.get_subcommands():
            name, cls = list(info)
            self.subcommands[name] = cls(name, self)

    def get_subcommands(self):
        # Populate in subclass
        return []


    def add_arguments(self, parser):
        super().add_arguments(parser)

        subcommand_help = [
            "{} {}:".format(self.command_color(self.get_full_name()), self.notice_color('command to execute')),
            ""
        ]
        for info in self.get_subcommands():
            subcommand = info[0]
            subcommand_help.extend(wrap(
                self.subcommands[subcommand].get_description(True),
                settings.DISPLAY_WIDTH - 25,
                init_indent = "{:2}{}  -  ".format(' ', self.command_color(subcommand)),
                init_style  = self.header_color(),
                indent      = "".ljust(2)
            ))
        parser.add_argument('subcommand', nargs=1, type=str, help="\n".join(subcommand_help))


    def handle(self, options):
        self.print_help()
