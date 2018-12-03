
from django.conf import settings
from django.db import connections
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.core.management.color import color_style

from settings import version
from utility.text import wrap, wrap_page

import os
import argparse
import re


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
        
        self.add_arguments(parser)
        return parser

    def server_enabled(self):
        return True

    def groups_allowed(self):
        return []

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

    def data(self, label, value, color = 'success', prnt = True):
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


    def run_from_argv(self, argv):
        self._called_from_command_line = True
        parser = self.create_parser(argv[0], argv[1])

        options = parser.parse_args(argv[2:])
        cmd_options = vars(options)
        args = cmd_options.pop('args', ())
        try:
            self.execute(*args, **cmd_options)
        except Exception as e:
            if not isinstance(e, CommandError):
                raise

            if isinstance(e, SystemCheckError):
                self.stderr.write(str(e), lambda x: x)
            else:
                self.stderr.write('%s: %s' % (e.__class__.__name__, e))
            sys.exit(1)
        finally:
            try:
                connections.close_all()
            except ImproperlyConfigured:
                pass
