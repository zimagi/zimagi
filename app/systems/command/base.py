from django.conf import settings
from django.db import connections
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.core.management.color import color_style

from rest_framework.compat import coreapi, coreschema
from rest_framework.schemas.inspectors import field_to_schema

from settings import version
from systems.command import args, messages, cli
from systems.command.mixins import data
from systems.api.schema import command
from utility.runtime import Runtime
from utility.config import Config
from utility.text import wrap, wrap_page
from utility.display import format_traceback
from utility.parallel import Thread

import sys
import os
import argparse
import re
import threading
import string


class OptionsTemplate(string.Template):
    delimiter = '@'
    idpattern = r'[a-z][\_\-a-z0-9]*'


class AppOptions(object):

    def __init__(self, command):
        self.command = command
        self._options = {}
        self.variables = None

    def init_variables(self):
        if self.variables is None:
            self.variables = {}
            
            if not self.command.active_user:
                for config in self.command._config.query():
                    self.variables[config.name] = config.value
            else:
                for config in self.command.get_instances(self.command._config):
                    self.variables[config.name] = config.value


    def get(self, name, default = None):
        return self._options.get(name, default)

    def add(self, name, value):
        self.init_variables()
        self._options[name] = self.interpolate(value)

    def interpolate(self, data):
        def _parse(value):
            parser = OptionsTemplate(value)
            try:
                return parser.substitute(**self.variables)
            except KeyError as e:
                self.command.error("Configuration {} does not exist, escape literal with @@".format(e))

        def _interpolate(value):
            if value:
                if isinstance(value, str):
                    value = _parse(value)
                elif isinstance(value, (list, tuple)):
                    for index, item in enumerate(value):
                        value[index] = _interpolate(value[index])     
                elif isinstance(value, dict):
                    for key, item in value.items():
                        value[key] = _interpolate(value[key])
            return value           

        return _interpolate(data)


    def rm(self, name):
        return self._options.pop(name)

    def clear(self):
        self._options.clear()

    def export(self):
        return self._options


class AppBaseCommand(
    data.EnvironmentMixin,
    data.ConfigMixin,
    BaseCommand
):
    def __init__(self, stdout = None, stderr = None, no_color = False):
        super().__init__(stdout, stderr, no_color)
        self.parent_command = None
        self.command_name = ''
        
        self.confirmation_message = 'Are you absolutely sure?'
        self.style = color_style()
        self.colorize = True
        self.messages = messages.MessageQueue()
        
        self.thread_lock = threading.Lock()

        self.schema = {}
        self.parser = None
        self.options = AppOptions(self)


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
            self.parse_debug()
            self.parse_color()
            self.colorize = not self.no_color
        
        self.parse()


    def parse_verbosity(self):
        name = 'verbosity'
        help_text = "\n".join(wrap("verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output", 40))

        self.add_schema_field(name, 
            args.parse_option(self.parser, 
                name, 'LEVEL', ('-v', '--verbosity'),
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
        help_text = "don't colorize the command output"

        self.add_schema_field(name, 
            args.parse_bool(self.parser, name, '--no-color', help_text), 
            True
        )

    @property
    def no_color(self):
        return self.options.get('no_color', False)


    def parse_debug(self):
        name = 'debug'
        help_text = "run in debug mode with error tracebacks"

        self.add_schema_field(name, 
            args.parse_bool(self.parser, name, '--debug', help_text), 
            True
        )


    def server_enabled(self):
        return True

    def remote_exec(self):
        return self.server_enabled()

    @property
    def api_exec(self):
        return settings.API_EXEC


    def groups_allowed(self):
        return False


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
        with self.thread_lock:
            msg = messages.InfoMessage(str(message), 
                name = name, 
                prefix = prefix,
                silent = False,
                colorize = not self.no_color
            )
            self.messages.add(msg)

            if not self.api_exec:
                msg.display()

    def data(self, label, value, name = None, prefix = None, silent = False):
        with self.thread_lock:
            msg = messages.DataMessage(str(label), value, 
                name = name, 
                prefix = prefix,
                silent = silent,
                colorize = not self.no_color
            )
            self.messages.add(msg)

            if not self.api_exec:
                msg.display()

    def silent_data(self, name, value):
        self.data(name, value, 
            name = name, 
            silent = True
        )
    
    def notice(self, message, name = None, prefix = None):
        with self.thread_lock:
            msg = messages.NoticeMessage(str(message), 
                name = name, 
                prefix = prefix,
                silent = False,
                colorize = not self.no_color
            )
            self.messages.add(msg)

            if not self.api_exec:
                msg.display()
    
    def success(self, message, name = None, prefix = None):
        with self.thread_lock:
            msg = messages.SuccessMessage(str(message), 
                name = name, 
                prefix = prefix,
                silent = False,
                colorize = not self.no_color
            )
            self.messages.add(msg)

            if not self.api_exec:
                msg.display()

    def warning(self, message, name = None, prefix = None):
        with self.thread_lock:
            msg = messages.WarningMessage(str(message), 
                name = name, 
                prefix = prefix,
                silent = False,
                colorize = not self.no_color
            )
            self.messages.add(msg)

            if not self.api_exec:
                msg.display()

    def error(self, message, name = None, prefix = None, terminate = True, traceback = None, error_cls = CommandError):
        with self.thread_lock:
            msg = messages.ErrorMessage(str(message),
                traceback = traceback,
                name = name, 
                prefix = prefix,
                silent = False,
                colorize = not self.no_color
            )
            if not traceback:
                msg.traceback = format_traceback()
            
            self.messages.add(msg)
        
        if not self.api_exec:
            msg.display()

        if terminate:
            raise error_cls(str(message))

    def table(self, data, name = None, prefix = None, silent = False):
        with self.thread_lock:
            msg = messages.TableMessage(data, 
                name = name, 
                prefix = prefix,
                silent = silent,
                colorize = not self.no_color
            )
            self.messages.add(msg)

            if not self.api_exec:
                msg.display()

    def silent_table(self, name, data):
        self.table(data, 
            name = name, 
            silent = True
        )

    def confirmation(self, message = None):
        if not self.api_exec and not self.force:
            if not message:
                message = self.confirmation_message
        
            confirmation = input("{} (type YES to confirm): ".format(message))    

            if re.match(r'^[Yy][Ee][Ss]$', confirmation):
                print('')
                return True
    
            self.error("User aborted", 'abort')


    def run_list(self, items, callback, state_callback = None, complete_callback = None):
        results = Thread(
            state_callback = state_callback,
            complete_callback = complete_callback
        ).list(items, callback)

        if results.aborted:
            for thread in results.errors:
                if not isinstance(thread.error, CommandError):
                    self.error("[ {} ] - {}".format(thread.name, thread.error), traceback = thread.traceback, terminate = False)
            
            self.error("Parallel run failed")

        return results


    def execute(self, *args, **options):
        if options['no_color']:
            self.style = no_style()
            self.stderr.style_func = None
        if options.get('stdout'):
            self.stdout = OutputWrapper(options['stdout'])
        if options.get('stderr'):
            self.stderr = OutputWrapper(options['stderr'], self.stderr.style_func)

        output = self.handle(*args, **options)
        if output:
            if self.output_transaction:
                connection = connections[options.get('database', DEFAULT_DB_ALIAS)]
                output = '%s\n%s\n%s' % (
                    self.style.SQL_KEYWORD(connection.ops.start_transaction_sql()),
                    output,
                    self.style.SQL_KEYWORD(connection.ops.end_transaction_sql()),
                )
            self.stdout.write(output)
        return output


    def run_from_argv(self, argv):
        Runtime.load(settings.RUNTIME_PATH)

        self._called_from_command_line = True

        prog_name = argv[0].replace('.py', '')
        parser = self.create_parser(prog_name, argv[1])

        if argv[1] != self.get_command_name():
            cmd_args = argv[1:]
        else:
            cmd_args = argv[2:]

        options = parser.parse_args(cmd_args)
        cmd_options = vars(options)
        args = cmd_options.pop('args', ())

        try:
            if cmd_options.get('debug', False):
                settings.DEBUG = cmd_options['debug']
            
            self.execute(*args, **cmd_options)
        
        finally:
            try:
                Runtime.save(settings.RUNTIME_PATH)
                connections.close_all()
            except ImproperlyConfigured:
                pass


    def find_command(self, full_name):
        command = re.split('\s+', full_name) if isinstance(full_name, str) else full_name
        utility = cli.AppManagementUtility()
        
        def find_command(components, command_tree, parents = []):
            name = components.pop(0)

            if name not in command_tree:
                self.error("Command {} {} not found".format(" ".join(parents), name))

            if len(components):
                parents.append(name)
                return find_command(components, command_tree[name]['sub'], parents)
            else:
                return command_tree[name]['cls']

        return find_command(command, utility.fetch_command_tree())
