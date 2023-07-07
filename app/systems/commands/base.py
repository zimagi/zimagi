from django.conf import settings
from django.db import connections
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import CommandError, CommandParser
from rest_framework.schemas.coreapi import field_to_schema

from settings.roles import Roles
from systems.encryption.cipher import Cipher
from systems.commands.index import CommandMixin
from systems.commands.mixins import query, relations, renderer
from systems.commands.schema import Field
from systems.commands import messages, help, options
from systems.api.command import schema
from utility.terminal import TerminalMixin
from utility.data import deep_merge, normalize_value, load_json
from utility.text import wrap_page
from utility.display import format_traceback
from utility.parallel import Parallel, ParallelError
from utility.filesystem import load_file
from utility.mutex import check_mutex, Mutex, MutexError, MutexTimeoutError
from utility.time import Time

import os
import signal
import threading
import time
import argparse
import re
import shutil
import queue
import copy
import logging
import cProfile


logger = logging.getLogger(__name__)


class BaseCommand(
    TerminalMixin,
    query.QueryMixin,
    relations.RelationMixin,
    renderer.RendererMixin,
    CommandMixin('user'),
    CommandMixin('environment'),
    CommandMixin('group'),
    CommandMixin('config'),
    CommandMixin('module')
):
    def __init__(self, name, parent = None):
        self.facade_index = {}

        self.name = name
        self.parent_instance = parent
        self.exec_parent = None

        self.time = Time()

        self.confirmation_message = 'Are you absolutely sure?'
        self.messages = queue.Queue()
        self.parent_messages = None
        self.mute = False

        self.schema = {}
        self.parser = None
        self.options = options.AppOptions(self)
        self.option_lock = threading.Lock()
        self.option_map = {}
        self.option_defaults = {}
        self.descriptions = help.CommandDescriptions()
        self._values = ({}, {})

        self.profilers = {}

        self.signal_list = [
            signal.SIGHUP,
            signal.SIGINT,
            signal.SIGTERM
        ]
        self.signal_handlers = {}

        super().__init__()

        if parent and parent.active_user:
            self._user.set_active_user(parent.active_user)


    def _signal_handler(self, sig, stack_frame):
        for lock_id in settings.MANAGER.index.get_locks():
            check_mutex(lock_id, force_remove = True).__exit__()

        for sig, handler in self.signal_handlers.items():
            signal.signal(sig, handler)

        os.kill(os.getpid(), sig)

    def _register_signal_handlers(self):
        for sig in self.signal_list:
            self.signal_handlers[sig] = (
                signal.signal(sig, self._signal_handler) or signal.SIG_DFL
            )


    def sleep(self, seconds):
        time.sleep(seconds)


    @property
    def manager(self):
        return settings.MANAGER

    @property
    def spec(self):
        return self.manager.get_spec(['command'] + self.get_full_name().split())

    @property
    def base_path(self):
        return self.manager.module_path

    @property
    def module_path(self):
        return os.path.join(self.base_path, self.spec['_module'])


    def get_path(self, path):
        return os.path.join(self.module_path, path)


    def queue(self, msg, log = True):
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
        return messages.AppMessage.get(data, decrypt = decrypt, user = self.active_user.name)

    def get_messages(self, flush = True):
        messages = []

        if flush:
            self.flush()

        for message in iter(self.messages.get, None):
            messages.append(message)
        return messages


    def add_schema_field(self, name, field, optional = True, tags = None, secret = False, system = False):
        if tags is None:
            tags = []

        self.schema[name] = Field(
            name = name,
            location = 'form',
            required = not optional,
            secret = secret,
            system = system,
            schema = field_to_schema(field),
            type = type(field).__name__.lower(),
            tags = tags
        )

    def get_schema(self):
        return schema.CommandSchema(list(self.schema.values()), re.sub(r'\s+', ' ', self.get_description(False)))


    def split_secrets(self, options = None):
        if options:
            secret_map = { key: field.secret for key, field in self.schema.items() }

            def strip_secret_tags(value):
                if isinstance(value, dict):
                    new_value = {}
                    for key, sub_value in value.items():
                        new_value[key.removeprefix(settings.SECRET_TOKEN)] = strip_secret_tags(sub_value)
                    return new_value
                elif isinstance(value, (list, tuple)):
                    for index, sub_value in enumerate(value):
                        value[index] = strip_secret_tags(sub_value)
                elif isinstance(value, str) and value.startswith(settings.SECRET_TOKEN):
                    return value.removeprefix(settings.SECRET_TOKEN)
                return value

            def replace_secrets(data_obj, check_secret_map = False):
                public = {}
                secrets = {}

                for key, value in data_obj.items():
                    if key.startswith(settings.SECRET_TOKEN):
                        key = key.removeprefix(settings.SECRET_TOKEN)
                        secrets[key] = strip_secret_tags(value)

                    elif isinstance(value, str) and value.startswith(settings.SECRET_TOKEN):
                        secrets[key] = normalize_value(
                            value.removeprefix(settings.SECRET_TOKEN),
                            parse_json = True
                        )

                    elif isinstance(value, dict):
                        sub_public, sub_secrets = replace_secrets(value)
                        public[key] = sub_public
                        if sub_secrets:
                            secrets[key] = sub_secrets

                    elif isinstance(value, (list, tuple)):
                        public[key] = []
                        secrets[key] = []

                        for sub_value in value:
                            if isinstance(sub_value, dict):
                                sub_public, sub_secrets = replace_secrets(sub_value)
                                public[key].append(sub_public if sub_public else None)
                                secrets[key].append(sub_secrets if sub_secrets else None)
                            elif isinstance(sub_value, str) and sub_value.startswith(settings.SECRET_TOKEN):
                                public[key].append(None)
                                secrets[key] = normalize_value(
                                    sub_value.removeprefix(settings.SECRET_TOKEN),
                                    parse_json = True
                                )
                            else:
                                public[key].append(sub_value)
                                secrets[key].append(None)

                        if len([ value for value in public[key] if value is not None ]) == 0:
                            public.pop(key)
                        if len([ value for value in secrets[key] if value is not None ]) == 0:
                            secrets.pop(key)

                    if not isinstance(value, (dict, list, tuple)):
                        if check_secret_map and secret_map.get(key, False):
                            secrets[key] = value
                        elif key not in secrets:
                            public[key] = value

                return public, secrets

            self._values = replace_secrets(options, True)
        return copy.deepcopy(self._values)


    def create_parser(self):

        def display_error(message):
            self.warning(message + "\n")
            self.print_help()
            self.exit(1)

        epilog = self.get_epilog()
        if epilog:
            epilog = "\n".join(wrap_page(epilog))

        parser = CommandParser(
            prog = self.command_color('zimagi {}'.format(self.get_full_name())),
            description = "\n".join(wrap_page(
                self.get_description(False),
                init_indent = ' ',
                init_style = self.header_color,
                indent = '  '
            )),
            epilog = epilog,
            formatter_class = argparse.RawTextHelpFormatter,
            called_from_command_line = True
        )
        parser.error = display_error

        self._user._ensure(self)
        self.add_arguments(parser)
        return parser

    def add_arguments(self, parser):
        self.parser = parser
        self.parse_base()


    def parse(self):
        # Override in subclass
        pass

    def parse_base(self, addons = None):
        self.option_map = {}

        if not self.parse_passthrough():
            # Display
            self.parse_verbosity()
            self.parse_debug()
            self.parse_display_width()
            self.parse_no_color()

            if not settings.API_EXEC:
                # Operations
                self.parse_version()

                if self.server_enabled():
                    self.parse_environment_host()

            # Operations
            self.parse_no_parallel()

            if addons and callable(addons):
                addons()

            self.parse()

    def parse_passthrough(self):
        return False


    def parse_environment_host(self):
        self.parse_variable('environment_host',
            '--host', str,
            "environment host name",
            value_label = 'NAME',
            default = settings.DEFAULT_HOST_NAME,
            tags = ['system']
        )

    @property
    def environment_host(self):
        return self.options.get('environment_host')


    def parse_verbosity(self):
        self.parse_variable('verbosity',
            '--verbosity', int,
            "verbosity level; 0=silent, 1=minimal, 2=normal, 3=verbose",
            value_label = 'LEVEL',
            default = 2,
            choices = (0, 1, 2, 3),
            tags = ['display']
        )

    @property
    def verbosity(self):
        verbosity = self.options.get('verbosity')
        if verbosity is None:
            verbosity = 2
        return verbosity

    def parse_version(self):
        self.parse_flag('version', '--version', "show environment runtime version information", tags = ['system'])

    def parse_display_width(self):
        self.parse_variable('display_width',
            '--display-width', int,
            "CLI display width",
            value_label = 'WIDTH',
            default = self.manager.runtime.width(),
            tags = ['display']
        )

    @property
    def display_width(self):
        width = self.options.get('display_width')
        if width is None:
            width = 80
        return width

    def parse_no_color(self):
        self.parse_flag('no_color', '--no-color', "don't colorize the command output",
            default = not self.manager.runtime.color(),
            tags = ['display']
        )

    @property
    def no_color(self):
        return self.options.get('no_color')

    def parse_debug(self):
        self.parse_flag('debug', '--debug', 'run in debug mode with error tracebacks',
            default = self.manager.runtime.debug(),
            tags = ['display']
        )

    @property
    def debug(self):
        return self.options.get('debug')

    def parse_no_parallel(self):
        self.parse_flag('no_parallel', '--no-parallel', 'disable parallel processing',
            default = not self.manager.runtime.parallel(),
            tags = ['system']
        )

    @property
    def no_parallel(self):
        return self.options.get('no_parallel')



    def interpolate_options(self):
        return True


    def server_enabled(self):
        return True

    def remote_exec(self):
        return self.server_enabled()

    def groups_allowed(self):
        return False


    def get_version(self):
        return settings.VERSION

    def get_priority(self):
        return 1


    def get_parent_name(self):
        if self.parent_instance and self.parent_instance.name != 'root':
            return self.parent_instance.get_full_name()
        return ''

    def get_full_name(self):
        return "{} {}".format(self.get_parent_name(), self.name).strip()

    def get_id(self):
        return ".".join(self.get_full_name().split(' '))

    def get_description(self, overview = False):
        return self.descriptions.get(self.get_full_name(), overview)

    def get_epilog(self):
        return None


    @property
    def active_user(self):
        return self._user.active_user if getattr(self, '_user', None) else None

    def check_execute(self, user):
        groups = self.groups_allowed()

        if not user:
            return False
        if user.name == settings.ADMIN_USER:
            return True

        if not groups:
            return True

        return user.env_groups.filter(name__in = groups).exists()


    def check_access(self, instance, reset = False):
        return self.check_access_by_groups(instance, instance.access_groups(reset))

    def check_access_by_groups(self, instance, groups):
        user_groups = [ Roles.admin ]

        if 'public' in groups:
            return True
        elif self.active_user is None:
            return False

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


    def get_provider(self, type, name, *args, facade = None, **options):
        base_provider = self.manager.index.get_plugin_base(type)
        providers = self.manager.index.get_plugin_providers(type, True)

        if name is None or name in ('help', 'base'):
            provider_class = base_provider
        elif name in providers.keys():
            provider_class = providers[name]
        else:
            self.error("Plugin {} provider {} not supported".format(type, name))

        try:
            provider = provider_class(type, name, self, *args, **options)
        except Exception as e:
            self.error("Plugin {} provider {} error: {}".format(type, name, e))

        if facade and provider.facade != facade:
            provider._facade = copy.deepcopy(facade)

        return provider


    def print_help(self, set_option_defaults = False):
        if set_option_defaults:
            self.set_option_defaults(False)

        parser = self.create_parser()
        self.info(parser.format_help())


    def message(self, msg, mutable = True, silent = False, log = True, verbosity = None):
        self.queue(msg, log = log)

        if mutable and self.mute:
            return
        if verbosity is None:
            verbosity = self.verbosity

        if not silent and (verbosity > 0 or msg.is_error()):
            display_options = {
                'debug': self.debug,
                'disable_color': self.no_color,
                'width': self.display_width
            }
            if msg.is_error():
                display_options['traceback'] = (verbosity > 1)

            msg.display(**display_options)


    def set_status(self, success, log = True):
        self.message(messages.StatusMessage(success,
                user = self.active_user.name if self.active_user else None
            ),
            log = log
        )


    def info(self, message, name = None, prefix = None, log = True):
        self.message(messages.InfoMessage(str(message),
                name = name,
                prefix = prefix,
                silent = False,
                user = self.active_user.name if self.active_user else None
            ),
            log = log
        )

    def data(self, label, value, name = None, prefix = None, silent = False, log = True):
        self.message(messages.DataMessage(str(label), value,
                name = name,
                prefix = prefix,
                silent = silent,
                user = self.active_user.name if self.active_user else None
            ),
            log = log
        )

    def silent_data(self, name, value, log = True):
        self.data(name, value,
            name = name,
            silent = True,
            log = log
        )

    def notice(self, message, name = None, prefix = None, log = True):
        self.message(messages.NoticeMessage(str(message),
                name = name,
                prefix = prefix,
                silent = False,
                user = self.active_user.name if self.active_user else None
            ),
            log = log
        )

    def success(self, message, name = None, prefix = None, log = True):
        self.message(messages.SuccessMessage(str(message),
                name = name,
                prefix = prefix,
                silent = False,
                user = self.active_user.name if self.active_user else None
            ),
            log = log
        )

    def warning(self, message, name = None, prefix = None, log = True):
        self.message(messages.WarningMessage(str(message),
                name = name,
                prefix = prefix,
                silent = False,
                user = self.active_user.name if self.active_user else None
            ),
            mutable = False,
            log = log
        )

    def error(self, message, name = None, prefix = None, terminate = True, traceback = None, error_cls = CommandError, silent = False):
        msg = messages.ErrorMessage(str(message),
            traceback = traceback,
            name = name,
            prefix = prefix,
            silent = silent,
            user = self.active_user.name if self.active_user else None
        )
        if not traceback:
            msg.traceback = format_traceback()

        self.message(msg,
            mutable = False,
            silent = silent
        )
        if terminate:
            raise error_cls(str(message))

    def table(self, data, name = None, prefix = None, silent = False, row_labels = False, log = True):
        self.message(messages.TableMessage(data,
                name = name,
                prefix = prefix,
                silent = silent,
                row_labels = row_labels,
                user = self.active_user.name if self.active_user else None
            ),
            log = log
        )

    def silent_table(self, name, data, log = True):
        self.table(data,
            name = name,
            silent = True,
            log = log
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
        public, secrets = self.split_secrets(data)
        params = {}

        for key, value in deep_merge(public, secrets, merge_lists = True, merge_null = False).items():
            if process_func and callable(process_func):
                key, value = process_func(key, value)

            if value is not None and value != '':
                if key in fields:
                    type = fields[key].type

                    if type in ('dictfield', 'listfield'):
                        params[key] = load_json(value)
                    elif type == 'booleanfield':
                        params[key] = load_json(value.lower())
                    elif type == 'integerfield':
                        params[key] = int(value)
                    elif type == 'floatfield':
                        params[key] = float(value)

                if key not in params:
                    params[key] = value
            else:
                params[key] = None

        return params


    def run_list(self, items, callback, *args, **kwargs):
        return Parallel.list(items, callback, *args,
            disable_parallel = self.no_parallel,
            command = self,
            **kwargs
        )

    def run_exclusive(self, lock_id, callback, error_on_locked = False, timeout = 600, interval = 1, run_once = False, force_remove = False):
        none_token = '<<<none>>>'
        results = None

        if not lock_id:
            results = callback()
        else:
            start_time = time.time()
            current_time = start_time

            while (current_time - start_time) <= timeout:
                try:
                    state_id = "lock_{}".format(lock_id)
                    if run_once:
                        results = self.get_state(state_id, None)
                        if results is not None:
                            if isinstance(results, str) and results == none_token:
                                results = None
                            break

                    with check_mutex(lock_id, force_remove = force_remove):
                        results = callback()
                        if run_once:
                            self.set_state(state_id, results if results is not None else none_token)
                        break

                except MutexError:
                    if error_on_locked:
                        self.error("Could not obtain lock for {}".format(lock_id))
                    if timeout == 0:
                        break

                except MutexTimeoutError:
                    logger.warning("Task {} completed but the lock timed out".format(lock_id))
                    break

                self.sleep(interval)
                current_time = time.time()

        return results


    def get_profiler_path(self, name):
        return os.path.join(self.manager.profiler_path, "{}.{}.profile".format(self.get_id(), name))

    def start_profiler(self, name):
        if settings.COMMAND_PROFILE:
            if name not in self.profilers:
                self.profilers[name] = cProfile.Profile()
            self.profilers[name].enable()

    def stop_profiler(self, name):
        if settings.COMMAND_PROFILE:
            self.profilers[name].disable()

    def export_profiler_data(self):
        if settings.COMMAND_PROFILE:
            for name, profiler in self.profilers.items():
                profiler.dump_stats(self.get_profiler_path(name))


    def ensure_resources(self, reinit = False):
        for facade_index_name in sorted(self.facade_index.keys()):
            if facade_index_name not in ['00_user']:
                self.facade_index[facade_index_name]._ensure(self, reinit = reinit)
        Mutex.set('startup')


    def set_option_defaults(self, parse_options = True):
        if parse_options:
            self.parse_base()

        for key, value in self.option_defaults.items():
            if not self.options.check(key):
                self.options.add(key, value)

    def validate_options(self, options):
        allowed_options = list(self.option_map.keys())
        not_found = []

        for key, value in options.items():
            if key not in allowed_options:
                not_found.append(key)

        if not_found:
            self.error("Requested command options not found: {}\n\nAvailable options: {}".format(
                ", ".join(not_found),
                ", ".join(allowed_options)
            ))

    def set_options(self, options, primary = False, split_secrets = True, custom = False, clear = True):
        if split_secrets:
            public, secrets = self.split_secrets(options)
            options = normalize_value(deep_merge(public, secrets, merge_lists = True, merge_null = False))

        if clear:
            self.options.clear()

        if not custom:
            if not primary or settings.API_EXEC:
                self.set_option_defaults()
                self.validate_options(options)

            host = options.pop('environment_host', None)
            if host:
                self.options.add('environment_host', host, False)

        for key, value in options.items():
            self.options.add(key, value)


    def bootstrap_ensure(self):
        return False

    def initialize_services(self):
        return True


    def bootstrap(self, options, split_secrets = True):
        Cipher.initialize()

        if options.get('debug', False):
            self.manager.runtime.debug(True)

        if options.get('no_parallel', False):
            self.manager.runtime.parallel(False)

        if options.get('no_color', False):
            self.manager.runtime.color(False)

        if options.get('display_width', False):
            self.manager.runtime.width(options.get('display_width'))

        self.init_environment()
        self.initialize(options, split_secrets = split_secrets)

        if self.initialize_services():
            self.manager.initialize_services(
                settings.STARTUP_SERVICES
            )
        return self

    def initialize(self, options = None, force = False, split_secrets = True):
        if force or (self.bootstrap_ensure() and settings.CLI_EXEC):
            self._user._ensure(self)

        if options:
            self.set_options(options, primary = True, split_secrets = split_secrets)

        if force or (self.bootstrap_ensure() and settings.CLI_EXEC):
            self.ensure_resources()


    def handle(self, options, primary = False):
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
                return self.print_help(True)

            options = vars(parser.parse_args(args))
        else:
            options = { 'args': args }

        try:
            self.bootstrap(options)
            self.handle(options, primary = True)
        finally:
            try:
                connections.close_all()
            except ImproperlyConfigured:
                pass

            self.export_profiler_data()
