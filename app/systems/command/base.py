from django.conf import settings
from django.db import connections
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import CommandError, CommandParser
from django.utils.module_loading import import_string

from rest_framework.compat import coreapi, coreschema
from rest_framework.schemas.inspectors import field_to_schema

from settings import version
from data.user.models import User
from systems.command import args, messages, registry
from systems.command.mixins import user, environment, group, config, module
from systems.api.schema import command
from utility.terminal import TerminalMixin
from utility.config import Config
from utility.runtime import Runtime
from utility.text import wrap, wrap_page
from utility.display import format_traceback
from utility.parallel import Parallel
from utility.data import deep_merge

import sys
import os
import argparse
import re
import shutil
import threading
import queue
import string
import copy
import yaml
import json


def command_list(*args):
    commands = []

    for arg in args:
        if isinstance(arg[0], (list, tuple)):
            commands.extend(arg)
        else:
            commands.append(arg)

    return commands


class CommandDescriptions(object):

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        if not getattr(self, '_initialized', False):
            self.thread_lock = threading.Lock()
            self.load()
            self._initialized = True


    def load(self):
        self.descriptions = {}

        def load_inner(data, help_path):
            for name in os.listdir(help_path):
                path = os.path.join(help_path, name)
                if os.path.isfile(path):
                    if path.endswith('.yml'):
                        with open(path, 'r') as file:
                            file_data = yaml.load(file.read())
                            deep_merge(data, file_data)
                else:
                    load_inner(data, path)

        with self.thread_lock:
            for help_dir in settings.LOADER.help_search_path():
                load_inner(self.descriptions, help_dir)

    def get(self, full_name, overview = True):
        with self.thread_lock:
            components = re.split(r'\s+', full_name)
            component_length = len(components)
            scope = self.descriptions

            for index, component in enumerate(components):
                if component in scope:
                    if index + 1 == component_length:
                        if overview:
                            return scope[component].get('overview', ' ')
                        else:
                            return scope[component].get('description', ' ')
                    else:
                        scope = scope[component]
        return ' '


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
            for config in self.command.get_instances(self.command._config):
                self.variables[config.name] = config.value

    def get(self, name, default = None):
        return self._options.get(name, default)

    def add(self, name, value):
        self.init_variables()
        env = self.command.get_env()

        if not env.host or (self.command.remote_exec() and Runtime.api()):
            self._options[name] = self.interpolate(value)
        else:
            self._options[name] = value

        return self._options[name]

    def interpolate(self, data):
        def _parse(value):
            if re.match(r'^@[a-z][\_\-a-z0-9]*$', value):
                value = value[1:]

                if value in self.variables:
                    return self.variables[value]

                self.command.error("Configuration {} does not exist, escape literal with @@".format(value))
            else:
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
    TerminalMixin,
    user.UserMixin,
    environment.EnvironmentMixin,
    group.GroupMixin,
    config.ConfigMixin,
    module.ModuleMixin
):
    def __init__(self, *args, **kwargs):
        self.facade_index = {}

        self.registry = registry.CommandRegistry()
        self.parent_command = None
        self.command_name = ''

        self.confirmation_message = 'Are you absolutely sure?'
        self.messages = queue.Queue()
        self.parent_messages = None

        self.thread_lock = threading.Lock()

        self.schema = {}
        self.parser = None
        self.options = AppOptions(self)
        self.descriptions = CommandDescriptions()

        super().__init__(*args, **kwargs)


    def queue(self, msg):
        data = msg.render()
        self.messages.put(data)
        if self.parent_messages:
            self.parent_messages.put(data)

    def flush(self):
        self.messages.put(None)

    def create_message(self, data, decrypt = True):
        msg = messages.AppMessage.get(data, decrypt = decrypt)
        return msg

    def get_messages(self, flush = True):
        messages = []

        if flush:
            self.flush()

        for message in iter(self.messages.get, None):
            messages.append(message)
        return messages


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


    def create_parser(self):

        def display_error(message):
            self.warning(message + "\n")
            self.print_help()
            self.exit(1)

        parser = CommandParser(
            prog = self.command_color('{} {}'.format(settings.APP_NAME, self.get_full_name())),
            description = "\n".join(wrap_page(
                self.get_description(False),
                init_indent = ' ',
                init_style = self.header_color(),
                indent = '  '
            )),
            formatter_class = argparse.RawTextHelpFormatter,
            called_from_command_line = True,
        )
        parser.error = display_error

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
        self.parse_no_parallel()
        self.parse_debug()
        self.parse_display_width()
        self.parse_color()

        if not Runtime.api():
            self.parse_version()

        self.parse()


    def parse_verbosity(self):
        self.parse_variable('verbosity',
            '--verbosity', int,
            "\n".join(wrap("verbosity level; 0=no output, 1=minimal output, 2=normal output, 3=verbose output", 60)),
            value_label = 'LEVEL',
            default = 2,
            choices = (0, 1, 2, 3)
        )

    @property
    def verbosity(self):
        return self.options.get('verbosity', 2)


    def parse_display_width(self):
        columns, rows = shutil.get_terminal_size(fallback = (settings.DISPLAY_WIDTH, 25))
        self.parse_variable('display_width',
            '--display-width', int,
            "CLI display width (default {} characters)".format(columns),
            value_label = 'WIDTH',
            default = columns
        )

    def parse_version(self):
        self.parse_flag('version', '--version', "show environment runtime version information")

    def parse_color(self):
        self.parse_flag('no_color', '--no-color', "don't colorize the command output")

    def parse_debug(self):
        self.parse_flag('debug', '--debug', 'run in debug mode with error tracebacks')

    def parse_no_parallel(self):
        self.parse_flag('no_parallel', '--no-parallel', 'disable parallel processing')


    def server_enabled(self):
        return True

    def remote_exec(self):
        return self.server_enabled()

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
        return self.descriptions.get(self.get_full_name(), overview)


    @property
    def active_user(self):
        return self._user.active_user

    def check_access(self, *groups):
        user_groups = []

        for group in groups:
            if isinstance(group, (list, tuple)):
                user_groups.extend(list(group))
            else:
                user_groups.append(group)

        if len(user_groups):
            if not self.active_user.env_groups.filter(name__in=user_groups).exists():
                self.warning("Operation requires at least one of the following roles in environment: {}".format(", ".join(user_groups)))
                return False

        return True


    def get_provider(self, type, name, *args, **options):
        type_components = type.split(':')
        type = type_components[0]
        subtype = type_components[1] if len(type_components) > 1 else None

        base_provider = settings.LOADER.provider_base(type)
        providers = settings.LOADER.providers(type, True)

        try:
            if name not in providers.keys() and name != 'help':
                raise Exception("Not supported")

            provider_class = providers[name] if name != 'help' else base_provider
            return import_string(provider_class)(type, name, self, *args, **options).context(subtype, self.test)

        except Exception as e:
            self.error("{} provider {} error: {}".format(type.title(), name, e))


    def print_help(self):
        parser = self.create_parser()
        self.info(parser.format_help())


    def info(self, message, name = None, prefix = None):
        with self.thread_lock:
            msg = messages.InfoMessage(str(message),
                name = name,
                prefix = prefix,
                silent = False
            )
            self.queue(msg)

            if not Runtime.api() and self.verbosity > 0:
                msg.display()

    def data(self, label, value, name = None, prefix = None, silent = False):
        with self.thread_lock:
            msg = messages.DataMessage(str(label), value,
                name = name,
                prefix = prefix,
                silent = silent
            )
            self.queue(msg)

            if not Runtime.api() and self.verbosity > 0:
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
                silent = False
            )
            self.queue(msg)

            if not Runtime.api() and self.verbosity > 0:
                msg.display()

    def success(self, message, name = None, prefix = None):
        with self.thread_lock:
            msg = messages.SuccessMessage(str(message),
                name = name,
                prefix = prefix,
                silent = False
            )
            self.queue(msg)

            if not Runtime.api() and self.verbosity > 0:
                msg.display()

    def warning(self, message, name = None, prefix = None):
        with self.thread_lock:
            msg = messages.WarningMessage(str(message),
                name = name,
                prefix = prefix,
                silent = False
            )
            self.queue(msg)

            if not Runtime.api() and self.verbosity > 0:
                msg.display()

    def error(self, message, name = None, prefix = None, terminate = True, traceback = None, error_cls = CommandError, silent = False):
        with self.thread_lock:
            msg = messages.ErrorMessage(str(message),
                traceback = traceback,
                name = name,
                prefix = prefix,
                silent = silent
            )
            if not traceback:
                msg.traceback = format_traceback()

            self.queue(msg)

        if not Runtime.api() and not silent:
            msg.display()

        if terminate:
            raise error_cls('')

    def table(self, data, name = None, prefix = None, silent = False):
        with self.thread_lock:
            msg = messages.TableMessage(data,
                name = name,
                prefix = prefix,
                silent = silent
            )
            self.queue(msg)

            if not Runtime.api() and self.verbosity > 0:
                msg.display()

    def silent_table(self, name, data):
        self.table(data,
            name = name,
            silent = True
        )

    def confirmation(self, message = None):
        if not Runtime.api() and not self.force:
            if not message:
                message = self.confirmation_message

            confirmation = input("{} (type YES to confirm): ".format(message))

            if re.match(r'^[Yy][Ee][Ss]$', confirmation):
                self.print()
                return True

            self.error("User aborted", 'abort')


    def format_fields(self, data, process_func = None):
        fields = self.get_schema().get_fields()
        params = {}

        for key, value in data.items():
            if process_func and callable(process_func):
                key, value = process_func(key, value)

            if value is not None and value != '':
                if key in fields:
                    type = fields[key].type

                    if type in ('dictfield', 'listfield'):
                        params[key] = json.loads(value)
                    elif type == 'booleanfield':
                        params[key] = json.loads(value.lower())
                    elif type == 'integerfield':
                        params[key] = int(value)
                    elif type == 'floatfield':
                        params[key] = float(value)

                if key not in params:
                    params[key] = value
            else:
                params[key] = None

        return params


    def run_list(self, items, callback):
        results = Parallel.list(items, callback)

        if results.aborted:
            for thread in results.errors:
                self.error(thread.error, prefix = "[ {} ] - ".format(thread.name), traceback = thread.traceback, terminate = False)

            self.error("Parallel run failed", silent = True)

        return results


    def ensure_resources(self):
        for facade_index_name in sorted(self.facade_index.keys()):
            self.facade_index[facade_index_name].ensure(self)

    def set_options(self, options):
        self.options.clear()
        for key, value in options.items():
            self.options.add(key, value)


    def bootstrap(self, options):
        if options.get('debug', False):
            Runtime.debug(True)

        if options.get('no_parallel', False):
            Runtime.parallel(False)

        if options.get('no_color', False):
            Runtime.color(False)

        if options.get('display_width', False):
            Runtime.width(options.get('display_width'))

        self.ensure_resources()
        self.set_options(options)

    def handle(self, options):
        # Override in subclass
        pass


    def run_from_argv(self, argv):
        parser = self.create_parser()
        args = argv[(len(self.get_full_name().split(' ')) + 1):]

        if '-h' in argv or '--help' in argv:
            self.print_help()
        else:
            options = vars(parser.parse_args(args))
            try:
                self.bootstrap(options)
                self.handle(options)
            finally:
                try:
                    connections.close_all()
                except ImproperlyConfigured:
                    pass
