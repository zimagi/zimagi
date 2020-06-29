from django.conf import settings
from django.db import connections
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import CommandError, CommandParser
from django.utils.module_loading import import_string

from db_mutex import DBMutexError, DBMutexTimeoutError
from db_mutex.models import DBMutex
from db_mutex.db_mutex import db_mutex

from rest_framework.compat import coreapi, coreschema
from rest_framework.schemas.coreapi import field_to_schema

from settings import version
from settings.roles import Roles
from data.environment.models import Environment
from data.user.models import User
from systems.commands.index import CommandMixin
from systems.commands.mixins import renderer
from systems.commands import args, messages, help, options
from systems.api.schema import command
from utility.terminal import TerminalMixin
from utility.runtime import Runtime
from utility.text import wrap, wrap_page
from utility.display import format_traceback
from utility.parallel import Parallel
from utility.data import deep_merge

import sys
import os
import time
import argparse
import re
import shutil
import threading
import queue
import string
import copy
import yaml
import json
import logging


logger = logging.getLogger(__name__)


class BaseCommand(
    TerminalMixin,
    renderer.RendererMixin,
    CommandMixin('user'),
    CommandMixin('environment'),
    CommandMixin('group'),
    CommandMixin('config'),
    CommandMixin('module')
):
    display_lock = threading.Lock()
    thread_lock = threading.Lock()


    def __init__(self, name, parent = None):
        self.facade_index = {}

        self.name = name
        self.parent_instance = parent
        self.exec_parent = None

        self.confirmation_message = 'Are you absolutely sure?'
        self.messages = queue.Queue()
        self.parent_messages = None
        self.mute = False

        self.schema = {}
        self.parser = None
        self.options = options.AppOptions(self)
        self.option_map = {}
        self.descriptions = help.CommandDescriptions()

        super().__init__()


    @property
    def manager(self):
        return settings.MANAGER


    def queue(self, msg):
        def _queue_parents(command, data):
            if command.parent_messages:
                command.parent_messages.put(data)
            if command.parent_instance:
                _queue_parents(command.parent_instance, data)

        data = msg.render()
        logger.debug("Adding command queue message: {}".format(data))

        self.messages.put(data)
        _queue_parents(self, data)
        return data

    def flush(self):
        logger.debug("Flushing command queue")
        self.messages.put(None)

    def create_message(self, data, decrypt = True):
        return messages.AppMessage.get(data, decrypt = decrypt)

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

        epilog = self.get_epilog()
        if epilog:
            epilog = "\n".join(wrap_page(epilog))

        parser = CommandParser(
            prog = self.command_color('{} {}'.format(settings.APP_NAME, self.get_full_name())),
            description = "\n".join(wrap_page(
                self.get_description(False),
                init_indent = ' ',
                init_style = self.header_color(),
                indent = '  '
            )),
            epilog = epilog,
            formatter_class = argparse.RawTextHelpFormatter,
            called_from_command_line = True
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
        self.option_map = {}

        if not self.parse_passthrough():
            self.parse_verbosity()
            self.parse_no_parallel()
            self.parse_no_color()
            self.parse_debug()
            self.parse_display_width()

            if not settings.API_EXEC:
                self.parse_environment_host()
                self.parse_version()

            self.parse()

    def parse_passthrough(self):
        return False


    def parse_environment_host(self):
        self.parse_variable('environment_host',
            '--host', str,
            "environment host name (default: {})".format(settings.DEFAULT_HOST_NAME),
            value_label = 'NAME',
            default = settings.DEFAULT_HOST_NAME
        )

    @property
    def environment_host(self):
        return self.options.get('environment_host', settings.DEFAULT_HOST_NAME)


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


    def parse_version(self):
        self.parse_flag('version', '--version', "show environment runtime version information")

    def parse_display_width(self):
        columns, rows = shutil.get_terminal_size(fallback = (settings.DISPLAY_WIDTH, 25))
        self.parse_variable('display_width',
            '--display-width', int,
            "CLI display width (default {} characters)".format(columns),
            value_label = 'WIDTH',
            default = columns
        )

    @property
    def display_width(self):
        return self.options.get('display_width', Runtime.width())

    def parse_no_color(self):
        self.parse_flag('no_color', '--no-color', "don't colorize the command output")

    @property
    def no_color(self):
        return self.options.get('no_color', not Runtime.color())

    def parse_debug(self):
        self.parse_flag('debug', '--debug', 'run in debug mode with error tracebacks')

    @property
    def debug(self):
        return self.options.get('debug', Runtime.debug())

    def parse_no_parallel(self):
        self.parse_flag('no_parallel', '--no-parallel', 'disable parallel processing')

    @property
    def no_parallel(self):
        return self.options.get('no_parallel', not Runtime.parallel())


    def interpolate_options(self):
        return True


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
        if self.parent_instance and self.parent_instance.name != 'root':
            return self.parent_instance.get_full_name()
        return ''

    def get_full_name(self):
        return "{} {}".format(self.get_parent_name(), self.name).strip()

    def get_description(self, overview = False):
        return self.descriptions.get(self.get_full_name(), overview)

    def get_epilog(self):
        return None


    @property
    def active_user(self):
        return self._user.active_user

    def check_access(self, instance, reset = False):
        return self.check_access_by_groups(instance, instance.access_groups(reset))

    def check_access_by_groups(self, instance, groups):
        user_groups = [ Roles.admin ]

        if not groups or self.active_user.name == settings.ADMIN_USER:
            return True

        for group in groups:
            if isinstance(group, (list, tuple)):
                user_groups.extend(list(group))
            else:
                user_groups.append(group)

        if len(user_groups):
            if not self.active_user.env_groups.filter(name__in = user_groups).exists():
                self.warning("Operation {} {} {} access requires at least one of the following roles in environment: {}".format(
                    self.get_full_name(),
                    instance.facade.name,
                    instance.name,
                    ", ".join(user_groups)
                ))
                return False

        return True


    def get_provider(self, type, name, *args, **options):
        type_components = type.split(':')
        type = type_components[0]
        subtype = type_components[1] if len(type_components) > 1 else None

        base_provider = self.manager.index.get_plugin_base(type)
        providers = self.manager.index.get_plugin_providers(type, True)

        if name is None or name in ('help', 'base'):
            provider_class = base_provider
        elif name in providers.keys():
            provider_class = providers[name]
        else:
            self.error("Plugin {} provider {} not supported".format(type, name))

        try:
            return provider_class(type, name, self, *args, **options).context(subtype, self.test)
        except Exception as e:
            self.error("Plugin {} provider {} error: {}".format(type, name, e))


    def print_help(self):
        parser = self.create_parser()
        self.info(parser.format_help())


    def info(self, message, name = None, prefix = None):
        with self.display_lock:
            if not self.mute:
                msg = messages.InfoMessage(str(message),
                    name = name,
                    prefix = prefix,
                    silent = False
                )
                self.queue(msg)

                if not settings.API_EXEC and self.verbosity > 0:
                    msg.display(
                        debug = self.debug,
                        disable_color = self.no_color,
                        width = self.display_width
                    )

    def data(self, label, value, name = None, prefix = None, silent = False):
        with self.display_lock:
            if not self.mute:
                msg = messages.DataMessage(str(label), value,
                    name = name,
                    prefix = prefix,
                    silent = silent
                )
                self.queue(msg)

                if not settings.API_EXEC and self.verbosity > 0:
                    msg.display(
                        debug = self.debug,
                        disable_color = self.no_color,
                        width = self.display_width
                    )

    def silent_data(self, name, value):
        self.data(name, value,
            name = name,
            silent = True
        )

    def notice(self, message, name = None, prefix = None):
        with self.display_lock:
            if not self.mute:
                msg = messages.NoticeMessage(str(message),
                    name = name,
                    prefix = prefix,
                    silent = False
                )
                self.queue(msg)

                if not settings.API_EXEC and self.verbosity > 0:
                    msg.display(
                        debug = self.debug,
                        disable_color = self.no_color,
                        width = self.display_width
                    )

    def success(self, message, name = None, prefix = None):
        with self.display_lock:
            if not self.mute:
                msg = messages.SuccessMessage(str(message),
                    name = name,
                    prefix = prefix,
                    silent = False
                )
                self.queue(msg)

                if not settings.API_EXEC and self.verbosity > 0:
                    msg.display(
                        debug = self.debug,
                        disable_color = self.no_color,
                        width = self.display_width
                    )

    def warning(self, message, name = None, prefix = None):
        with self.display_lock:
            msg = messages.WarningMessage(str(message),
                name = name,
                prefix = prefix,
                silent = False
            )
            self.queue(msg)

            if not settings.API_EXEC and self.verbosity > 0:
                msg.display(
                    debug = self.debug,
                    disable_color = self.no_color,
                    width = self.display_width
                )

    def error(self, message, name = None, prefix = None, terminate = True, traceback = None, error_cls = CommandError, silent = False):
        with self.display_lock:
            msg = messages.ErrorMessage(str(message),
                traceback = traceback,
                name = name,
                prefix = prefix,
                silent = silent
            )
            if not traceback:
                msg.traceback = format_traceback()

            self.queue(msg)

            if not settings.API_EXEC and not silent:
                msg.display(
                    debug = self.debug,
                    disable_color = self.no_color,
                    width = self.display_width
                )

        if terminate:
            raise error_cls('')

    def table(self, data, name = None, prefix = None, silent = False, row_labels = False):
        with self.display_lock:
            if not self.mute:
                msg = messages.TableMessage(data,
                    name = name,
                    prefix = prefix,
                    silent = silent,
                    row_labels = row_labels
                )
                self.queue(msg)

                if not settings.API_EXEC and self.verbosity > 0:
                    msg.display(
                        debug = self.debug,
                        disable_color = self.no_color,
                        width = self.display_width
                    )

    def silent_table(self, name, data):
        self.table(data,
            name = name,
            silent = True
        )

    def confirmation(self, message = None):
        if not settings.API_EXEC and not self.force:
            if not message:
                message = self.confirmation_message

            confirmation = input("{} (type YES to confirm): ".format(message))

            if re.match(r'^[Yy][Ee][Ss]$', confirmation):
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
        results = Parallel.list(items, callback, disable_parallel = self.no_parallel)

        if results.aborted:
            for thread in results.errors:
                self.error(thread.error, prefix = "[ {} ]".format(thread.name), traceback = thread.traceback, terminate = False)

            self.error("Parallel run failed", silent = True)

        return results

    def run_exclusive(self, lock_id, callback, error_on_locked = False, wait = True, timeout = 600, interval = 2):
        if not lock_id:
            callback()
        else:
            start_time = time.time()
            current_time = start_time

            while (current_time - start_time) <= timeout:
                try:
                    with db_mutex(lock_id):
                        callback()
                        break

                except DBMutexError:
                    if error_on_locked:
                        self.error("Could not obtain lock for {}".format(lock_id))
                    if not wait:
                        break

                except DBMutexTimeoutError:
                    logger.warning("Task {} completed but the lock timed out".format(lock_id))
                    break

                except Exception as e:
                    DBMutex.objects.filter(lock_id = lock_id).delete()
                    raise e

                time.sleep(interval)
                current_time = time.time()


    def ensure_resources(self):
        for facade_index_name in sorted(self.facade_index.keys()):
            if facade_index_name not in ['00_environment', '00_user']:
                self.facade_index[facade_index_name]._ensure(self)

    def set_options(self, options):
        self.options.clear()

        host = options.pop('environment_host', None)
        if host:
           self.options.add('environment_host', host, False)

        for key, value in options.items():
            self.options.add(key, value)


    def bootstrap(self, options, primary = False):
        if primary:
            if options.get('debug', False):
                Runtime.debug(True)

            if options.get('no_parallel', False):
                Runtime.parallel(False)

            if options.get('no_color', False):
                Runtime.color(False)

            if options.get('display_width', False):
                Runtime.width(options.get('display_width'))

        self._environment._ensure(self)
        self._user._ensure(self)

        self.set_options(options)
        if primary:
            self.ensure_resources()

    def handle(self, options):
        # Override in subclass
        pass


    def run_from_argv(self, argv):
        parser = self.create_parser()
        args = argv[(len(self.get_full_name().split(' ')) + 1):]

        if not self.parse_passthrough():
            if '--version' in argv:
                return self.manager.index.find_command(
                    'version',
                    main = True
                ).run_from_argv([])

            elif '-h' in argv or '--help' in argv:
                return self.print_help()

            options = vars(parser.parse_args(args))
        else:
            options = { 'args': args }

        try:
            self.bootstrap(options, True)
            self.handle(options, True)
        finally:
            try:
                connections.close_all()
            except ImproperlyConfigured:
                pass
