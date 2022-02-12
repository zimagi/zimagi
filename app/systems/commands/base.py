from django.conf import settings
from django.db import connections
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import CommandError, CommandParser
from rest_framework.schemas.coreapi import field_to_schema

from settings.roles import Roles
from systems.encryption.cipher import Cipher
from systems.commands.index import CommandMixin
from systems.commands.mixins import renderer
from systems.commands.schema import Field
from systems.commands import messages, help, options
from systems.api.command import schema
from utility.terminal import TerminalMixin
from utility.runtime import Runtime
from utility.data import load_json
from utility.text import wrap_page
from utility.display import format_traceback
from utility.parallel import Parallel, ParallelError
from utility.filesystem import load_file
from utility.mutex import check_mutex, MutexError, MutexTimeoutError

import os
import signal
import threading
import pathlib
import time
import argparse
import re
import shutil
import queue
import logging
import cProfile


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
        self.option_lock = threading.Lock()
        self.option_map = {}
        self.option_defaults = {}
        self.descriptions = help.CommandDescriptions()

        self.profilers = {}

        self.signal_list = [
            signal.SIGHUP,
            signal.SIGINT,
            signal.SIGTERM
        ]
        self.signal_handlers = {}

        super().__init__()


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
        env = self.get_env()
        return os.path.join(settings.MODULE_BASE_PATH, env.name)

    @property
    def module_path(self):
        return "{}/{}".format(self.base_path, self.spec['_module'])


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


    def add_schema_field(self, name, field, optional = True, tags = None):
        if tags is None:
            tags = []

        self.schema[name] = Field(
            name = name,
            location = 'form',
            required = not optional,
            schema = field_to_schema(field),
            type = type(field).__name__.lower(),
            tags = tags
        )

    def get_schema(self):
        return schema.CommandSchema(list(self.schema.values()), re.sub(r'\s+', ' ', self.get_description(False)))


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
        return self.options.get('environment_host', settings.DEFAULT_HOST_NAME)


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
        return self.options.get('verbosity', 2)


    def parse_version(self):
        self.parse_flag('version', '--version', "show environment runtime version information", tags = ['system'])

    def parse_display_width(self):
        columns, rows = shutil.get_terminal_size(fallback = (settings.DISPLAY_WIDTH, 25))
        self.parse_variable('display_width',
            '--display-width', int,
            "CLI display width",
            value_label = 'WIDTH',
            default = columns,
            tags = ['display']
        )

    @property
    def display_width(self):
        return self.options.get('display_width', Runtime.width())

    def parse_no_color(self):
        self.parse_flag('no_color', '--no-color', "don't colorize the command output", tags = ['display'])

    @property
    def no_color(self):
        return self.options.get('no_color', not Runtime.color())

    def parse_debug(self):
        self.parse_flag('debug', '--debug', 'run in debug mode with error tracebacks', tags = ['display'])

    @property
    def debug(self):
        return self.options.get('debug', Runtime.debug())

    def parse_no_parallel(self):
        self.parse_flag('no_parallel', '--no-parallel', 'disable parallel processing', tags = ['system'])

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
        if not getattr(self, '_version'):
            self._version = load_file(os.path.join(self.manager.app_dir, 'VERSION'))
        return self._version

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

    def check_execute(self, user = None):
        groups = self.groups_allowed()
        user = self.active_user if user is None else user

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


    def message(self, msg, mutable = True, silent = False, log = True, verbosity = None):
        if mutable and self.mute:
            return

        if verbosity is None:
            verbosity = self.verbosity

        if not silent and (verbosity > 0 or msg.is_error()):
            self.queue(msg, log = log)

            if settings.CLI_EXEC or settings.SERVICE_INIT or self.debug:
                display_options = {
                    'debug': self.debug,
                    'disable_color': self.no_color,
                    'width': self.display_width
                }
                if msg.is_error():
                    display_options['traceback'] = (verbosity > 1)

                msg.display(**display_options)


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
        params = {}

        for key, value in data.items():
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


    def run_list(self, items, callback):
        results = Parallel.list(items, callback, disable_parallel = self.no_parallel)

        if results.aborted:
            for thread in results.errors:
                self.error(thread.error, prefix = "[ {} ]".format(thread.name), traceback = thread.traceback, terminate = False)
            raise ParallelError()

        return results

    def run_exclusive(self, lock_id, callback, error_on_locked = False, timeout = 600, interval = 1, run_once = False):
        if not lock_id:
            callback()
        else:
            start_time = time.time()
            current_time = start_time

            while (current_time - start_time) <= timeout:
                try:
                    state_id = "lock_{}".format(lock_id)
                    if run_once and self.get_state(state_id, None):
                        break

                    with check_mutex(lock_id):
                        callback()
                        if run_once:
                            self.set_state(state_id, current_time)
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


    def get_profiler_path(self, name):
        base_path = os.path.join(settings.PROFILER_PATH, self.curr_env_name)
        pathlib.Path(base_path).mkdir(parents = True, exist_ok = True)
        return os.path.join(base_path, "{}.{}.profile".format(self.get_id(), name))

    def start_profiler(self, name, check = True):
        if settings.COMMAND_PROFILE and settings.CLI_EXEC and check:
            if name not in self.profilers:
                self.profilers[name] = cProfile.Profile()
            self.profilers[name].enable()

    def stop_profiler(self, name, check = True):
        if settings.COMMAND_PROFILE and settings.CLI_EXEC and check:
            self.profilers[name].disable()

    def export_profiler_data(self):
        if settings.COMMAND_PROFILE and settings.CLI_EXEC:
            command_id = self.get_id()
            for name, profiler in self.profilers.items():
                profiler.dump_stats(self.get_profiler_path(name))


    def ensure_resources(self, reinit = False):
        for facade_index_name in sorted(self.facade_index.keys()):
            if facade_index_name not in ['00_user']:
                self.facade_index[facade_index_name]._ensure(self, reinit = reinit)


    def set_option_defaults(self):
        self.parse_base()

        for key, value in self.option_defaults.items():
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

    def set_options(self, options, primary = False):
        self.options.clear()

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


    def bootstrap(self, options):
        Cipher.initialize()

        if options.get('debug', False):
            Runtime.debug(True)

        if options.get('no_parallel', False):
            Runtime.parallel(False)

        if options.get('no_color', False):
            Runtime.color(False)

        if options.get('display_width', False):
            Runtime.width(options.get('display_width'))

        self.init_environment()

        if self.bootstrap_ensure() and settings.CLI_EXEC:
            self._user._ensure(self)

        self.set_options(options, True)

        if self.bootstrap_ensure() and settings.CLI_EXEC:
            self.ensure_resources()

        if self.initialize_services():
            self.manager.initialize_services(
                settings.STARTUP_SERVICES
            )
        return self

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
                return self.print_help()

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
