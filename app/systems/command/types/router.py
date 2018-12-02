
from django.conf import settings
from django.core.management.base import CommandError

from systems.command import base
from utility.text import wrap

import sys
import re


class RouterCommand(base.AppBaseCommand):
    
    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout, stderr, no_color)
        self.init_subcommand_instances(stdout, stderr, no_color)

    
    def add_arguments(self, parser):
        super().add_arguments(parser)

        subcommand_help = [
            "{} {}:".format(self.style.SUCCESS(self.get_full_name()), self.style.NOTICE('command to execute')),
            ""
        ]
        for info in self.get_subcommands():
            subcommand = info[0]
            subcommand_help.extend(wrap(
                self.subcommands[subcommand].get_description(True), 
                settings.DISPLAY_WIDTH - 25,
                init_indent = "{:2}{}  -  ".format(' ', self.style.SUCCESS(subcommand)),
                init_style  = self.style.WARNING,
                indent      = "".ljust(2)
            ))
        
        parser.add_argument('subcommand', nargs=1, type=str, help="\n".join(subcommand_help))


    def run_from_argv(self, argv):
        subcommand = argv[2:][0] if len(argv) > 2 else None
        status = 0

        if re.match(r'^\.', argv[0]):
            argv[0] = settings.APP_NAME

        if subcommand:
            if subcommand in self.subcommands:
                subargs = argv[1:]
                subargs[0] = "{} {}".format(argv[0], subargs[0])
                return self.subcommands[subcommand].run_from_argv(subargs)
            else:
                print(self.style.ERROR("Unknown subcommand: {} (see below for options)\n".format(subcommand)))
                status = 1
        
        self.print_help(argv[0], argv[1:])
        sys.exit(status)


    def get_subcommands(self):
        # Populate in subclass
        return []

    def init_subcommand_instances(self, stdout, stderr, no_color):
        self.subcommands = {}

        for info in self.get_subcommands():
            name, cls = list(info)
            subcommand = cls(stdout, stderr, no_color)
            
            subcommand.parent_command = self
            subcommand.command_name = name

            self.subcommands[name] = subcommand


    def print_help(self, prog_name, args):
        command = args[0]
        subcommand = args[1] if len(args) > 1 else None
        
        if subcommand and subcommand in self.subcommands:
            self.subcommands[subcommand].print_help(
                "{} {}".format(prog_name, command), 
                args[1:]
            )
        else:
            super().print_help(prog_name, args)


    def handle(self, *args, **options):
        subcommand = options['subcommand'][0]
        
        if subcommand in self.subcommands:
            return self.subcommands[subcommand].handle(*args, **options)
        else:
            self.print_help(settings.APP_NAME, [self.get_full_name()])
            print("\n")
            raise CommandError("subcommand {} not found. See help above for available options".format(subcommand))
