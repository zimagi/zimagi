
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError, CommandParser, DjangoHelpFormatter
from django.core.management.color import color_style

from settings import version
from utility.text import wrap, wrap_page
from utility.display import print_table

import os
import sys
import argparse
import re
import json


class AppBaseCommand(BaseCommand):

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout, stderr, no_color)
        self.parent_command = None
        self.command_name = ''
        self.style = color_style()


    def create_parser(self, prog_name, subcommand):
        parser = CommandParser(
            prog=self.style.SUCCESS('{} {}'.format(os.path.basename(prog_name), subcommand)),
            description="\n".join(wrap_page(
                self.get_description(False), 
                init_indent = ' ', 
                init_style = self.style.WARNING,
                indent = '  '
            )),
            formatter_class=argparse.RawTextHelpFormatter,
            missing_args_message=getattr(self, 'missing_args_message', None),
            called_from_command_line=getattr(self, '_called_from_command_line', None),
        )

        parser.add_argument('--version', action='version', version=self.get_version())
        parser.add_argument(
            '-v', '--verbosity', action='store', dest='verbosity', default=1,
            type=int, choices=[0, 1, 2, 3],
            help="\n".join(wrap("verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output", 40))
        )
        parser.add_argument(
            '--no-color', action='store_true', dest='no_color',
            help="don't colorize the command output.",
        )

        # Hidden options
        parser.add_argument('--settings', help=argparse.SUPPRESS)
        parser.add_argument('--pythonpath', help=argparse.SUPPRESS)
        parser.add_argument('--traceback', action='store_true', help=argparse.SUPPRESS)

        self.add_arguments(parser)
        return parser


    def get_version(self):
        return version.VERSION

    def get_priority(self):
        return 1

    def get_parent_name(self):
        if self.parent_command:
            return self.parent_command.get_full_name()
        return ''

    def get_command_name(self):
        # Populate root command in subclass 
        #  or subcommands are autopopulated by parent
        return self.command_name

    def get_full_name(self):
        return "{} {}".format(self.get_parent_name(), self.get_command_name()).strip()


    def get_description(self, overview = False):
        return ''


    def print_help(self, prog_name, args):
        parser = self.create_parser(prog_name, args[0])
        parser.print_help()
    

    def info(self, message, prnt = True):
        if prnt:
            print(message)
        return message

    def data(self, label, value, color = 'success', prnt = True)
        return self.info("{}: {}".format(
            label, 
            self.color(value, color)
        ), prnt)
    
    def notice(self, message, prnt = True):
        text = self.style.NOTICE(message)
        return self.info(text, prnt)

    def success(self, message, prnt = True):
        text = self.style.SUCCESS(message)
        return self.info(text, prnt)

    def color(self, message, type = 'success'):
        return getattr(self, type)(message, False)


    def _exception(self, message, throw = True):
        if throw:
            raise CommandError(message)
        return message

    def warning(self, message, throw = True):
        text = self.style.WARNING(message)
        return self._exception(text, throw)

    def error(self, message, throw = True):
        text = self.style.ERROR(message)
        return self._exception(text, throw)


    def confirmation(self, message = '', throw = True):
        if not message:
            message = "Are you sure?"
        
        confirmation = input("{} (type YES to confirm): ".format(message))    

        if re.match(r'^[Yy][Ee][Ss]$', confirmation):
            return True
    
        self.warning("User aborted", throw)
        return False


class SimpleCommand(AppBaseCommand):

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout, stderr, no_color)
        self.parser = None
        self.args = None
        self.options = None


    def parse(self):
        # Override in subclass
        pass

    def add_arguments(self, parser):
        super().add_arguments(parser)

        self.parser = parser
        self.parse()


    def exec(self):
        # Override in subclass
        pass

    def handle(self, *args, **options):
        self.args = args
        self.options = options
        self.exec()


    def print_table(self, data):
        print_table(data)


class ComplexCommand(AppBaseCommand):
    
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
