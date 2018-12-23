from django.conf import settings
from django.db import connections
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.core.management.color import color_style

from rest_framework.compat import coreapi, coreschema
from rest_framework.schemas.inspectors import field_to_schema

from settings import version
from systems.command import args
from systems.command import messages
from systems.api.schema import command
from utility.text import wrap, wrap_page

import sys
import os
import argparse
import re


class AppOptions(object):

    def __init__(self):
        self._options = {}


    def get(self, name, default = None):
        return self._options.get(name, default)

    def add(self, name, value):
        self._options[name] = value

    def rm(self, name):
        return self._options.pop(name)

    def clear(self):
        self._options.clear()

    @property
    def export(self):
        return self._options       


class AppBaseCommand(BaseCommand):

    def __init__(self, stdout = None, stderr = None, no_color = False):
        super().__init__(stdout, stderr, no_color)
        self.parent_command = None
        self.command_name = ''
        
        self.api_exec = False

        self.confirmation_message = 'Are you absolutely sure?'
        self.style = color_style()
        self.colorize = True
        self.messages = messages.MessageQueue()
        
        self.schema = {}
        self.options = AppOptions()
        self.parser = None


    def add_schema_field(self, name, field, optional = True):
        self.schema[name] = coreapi.Field(
            name = name,
            location = 'form',
            required = not optional,
            schema = field_to_schema(field),
            type = type(field).__name__.lower()
        )

    def get_schema(self):
        return command.CommandSchema(list(self.schema.values()), re.sub(r'\s+', ' ', self.get_description(False)))


    def create_parser(self, prog_name, subcommand):
        parser = CommandParser(
            prog = self.style.SUCCESS('{} {}'.format(os.path.basename(prog_name), subcommand)),
            description = "\n".join(wrap_page(
                self.get_description(False), 
                init_indent = ' ', 
                init_style = self.style.WARNING,
                indent = '  '
            )),
            formatter_class = argparse.RawTextHelpFormatter,
            missing_args_message = getattr(self, 'missing_args_message', None),
            called_from_command_line = getattr(self, '_called_from_command_line', None),
        )
        parser.add_argument('--version', action='version', version=self.get_version())
        
        self.add_arguments(parser)
        return parser

    def add_arguments(self, parser):
        self.parser = parser
        self.parse_base()


    def parse(self):
        # Override in subclass
        pass

    def parse_base(self):
        self.parse_verbosity()

        if not self.api_exec:
            self.parse_color()
            self.colorize = not self.no_color
        
        self.parse()


    def parse_verbosity(self):
        name = 'verbosity'
        help_text = "\n".join(wrap("verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output", 40))

        self.add_schema_field(name, 
            args.parse_option(self.parser, 
                name, ('-v', '--verbosity'),
                int, help_text, 
                1, (0, 1, 2, 3)
            ), 
            True
        )

    @property
    def verbosity(self):
        return self.options.get('verbosity', 1)


    def parse_color(self):
        name = 'no_color'
        help_text = "don't colorize the command output."

        self.add_schema_field(name, 
            args.parse_bool(self.parser, name, '--no-color', help_text), 
            True
        )

    @property
    def no_color(self):
        return self.options.get('no_color', False)


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
    

    def info(self, message, name = None, prefix = None):
        msg = messages.InfoMessage(str(message), name, prefix)
        msg.colorize = not self.no_color
        
        self.messages.add(msg)

        if not self.api_exec:
            msg.display()

    def data(self, label, value, name = None, prefix = None):
        msg = messages.DataMessage(str(label), value, name, prefix)
        msg.colorize = not self.no_color
        
        self.messages.add(msg)

        if not self.api_exec:
            msg.display()
    
    def notice(self, message, name = None, prefix = None):
        msg = messages.NoticeMessage(str(message), name, prefix)
        msg.colorize = not self.no_color
        
        self.messages.add(msg)

        if not self.api_exec:
            msg.display()
    
    def success(self, message, name = None, prefix = None):
        msg = messages.SuccessMessage(str(message), name, prefix)
        msg.colorize = not self.no_color
        
        self.messages.add(msg)

        if not self.api_exec:
            msg.display()

    def warning(self, message, name = None, prefix = None):
        msg = messages.WarningMessage(str(message), name, prefix)
        msg.colorize = not self.no_color
        
        self.messages.add(msg)

        if not self.api_exec:
            msg.display()

    def error(self, message, name = None, prefix = None):
        msg = messages.ErrorMessage(str(message), name, prefix)
        msg.colorize = not self.no_color
        
        self.messages.add(msg)

        if not self.api_exec:
            msg.display()
        
        raise CommandError(str(message))

    def table(self, data, name = None, prefix = None):
        msg = messages.TableMessage(data, name, prefix)
        msg.colorize = not self.no_color
        
        self.messages.add(msg)

        if not self.api_exec:
            msg.display()


    def confirmation(self, message = None):
        if not self.api_exec:
            if not message:
                message = self.confirmation_message
        
            confirmation = input("{} (type YES to confirm): ".format(message))    

            if re.match(r'^[Yy][Ee][Ss]$', confirmation):
                return True
    
            self.error("User aborted", 'abort')


    def run_from_argv(self, argv):
        self.parse_base()

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
            
            sys.exit(1)
        
        finally:
            try:
                connections.close_all()
            except ImproperlyConfigured:
                pass
