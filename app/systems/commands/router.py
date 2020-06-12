from collections import OrderedDict

from django.conf import settings
from django.core.management.base import CommandError

from systems.commands import base
from utility.text import wrap

import sys
import re
import inspect


class RouterCommand(base.BaseCommand):

    def __init__(self, name, parent = None, priority = 1):
        super().__init__(name, parent)

        self._priority = priority
        self._subcommands = OrderedDict()
        self.is_empty = True


    def get_priority(self):
        return self._priority


    def get_subcommands(self):
        command_index = {}
        subcommands = []

        for name, subcommand in self._subcommands.items():
            priority = subcommand.get_priority()
            command_index.setdefault(priority, [])
            command_index[priority].append(subcommand)

        for priority in sorted(command_index.keys()):
            subcommands.extend(command_index[priority])

        return subcommands

    def exists(self, name):
        return name in self._subcommands


    def __getitem__(self, name):
        return self._subcommands[name]

    def get(self, name, default = None):
        return self._subcommands.get(name, default)

    def __setitem__(self, name, command):
        self.is_empty = False

        if inspect.isclass(command):
            self._subcommands[name] = command(name, self)
        else:
            self._subcommands[name] = command


    def add_arguments(self, parser):
        super().add_arguments(parser)

        subcommand_help = [
            "{} {}:".format(self.command_color(self.get_full_name()), self.notice_color('command to execute')),
            ""
        ]
        for subcommand in self.get_subcommands():
            subcommand_help.extend(wrap(
                subcommand.get_description(True),
                settings.DISPLAY_WIDTH - 25,
                init_indent = "{:2}{}  -  ".format(' ', self.command_color(subcommand.name)),
                init_style  = self.header_color(),
                indent      = "".ljust(2)
            ))
        parser.add_argument('subcommand',
            nargs = 1,
            type = str,
            help = "\n".join(subcommand_help)
        )


    def handle(self, options):
        self.print_help()


    def __str__(self):
        return "Router <{}>".format(self.name)
