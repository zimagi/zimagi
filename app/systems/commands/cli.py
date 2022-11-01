from django.conf import settings
from django.db import connection
from django.core import management
from django.core.management import call_command
from django.core.management.base import CommandError, CommandParser
from django.core.management.commands import migrate

from systems.models.overrides import *
from utility.terminal import TerminalMixin
from utility.display import format_exception_info
from utility.mutex import check_mutex, MutexError


import functools
import django
import os
import sys
import pathlib
import time
import cProfile


django_allowed_commands = [
    'check',
    'shell',
    'dbshell',
    'inspectdb',
    'showmigrations',
    'makemigrations',
    'migrate'
]


class CLI(TerminalMixin):

    def __init__(self, argv = None):
        super().__init__()
        self.argv = argv if argv else []


    def handle_error(self, error):
        if not isinstance(error, CommandError) and error.args:
            self.print('** ' + self.error_color(error.args[0]), sys.stderr)
            try:
                debug = settings.MANAGER.runtime.debug()
            except AttributeError:
                debug = True

            if debug:
                self.print('> ' + self.traceback_color(
                        "\n".join([ item.strip() for item in format_exception_info() ])
                    ),
                    stream = sys.stderr
                )


    def exclusive_wrapper(self, exec_method, lock_id):
        def wrapper(*args, **kwargs):
            tries = 0
            while True:
                try:
                    with check_mutex(lock_id):
                        if tries == 0:
                            return exec_method(*args, **kwargs)
                        return

                except MutexError as error:
                    pass

                time.sleep(0.1)
                tries += 1

        functools.update_wrapper(wrapper, exec_method)
        return wrapper


    def initialize(self):
        django.setup()

        parser = CommandParser(add_help = False, allow_abbrev = False)
        parser.add_argument('args', nargs = '*')
        namespace, extra = parser.parse_known_args(self.argv[1:])
        args = namespace.args

        if not args:
            args = ['help']

        if '--debug' in extra:
            settings.MANAGER.runtime.debug(True)

        if '--no-color' in extra:
            settings.MANAGER.runtime.color(False)

        if not settings.NO_MIGRATE and args and args[0] not in ('check', 'migrate', 'makemigrations'):
            verbosity = 3 if settings.MANAGER.runtime.debug() else 0
            start_time = time.time()
            current_time = start_time

            while (current_time - start_time) <= settings.AUTO_MIGRATE_TIMEOUT:
                try:
                    call_command('migrate', interactive = False, verbosity = verbosity)
                    break
                except Exception as error:
                    self.print(str(error))
                    pass

                time.sleep(settings.AUTO_MIGRATE_INTERVAL)
                current_time = time.time()

        return args


    def execute(self):
        try:
            if settings.INIT_PROFILE or settings.COMMAND_PROFILE:
                settings.MANAGER.runtime.parallel(False)

            if settings.COMMAND_PROFILE:
                command_profiler = cProfile.Profile()

            if settings.INIT_PROFILE:
                init_profiler = cProfile.Profile()
                init_profiler.enable()

            try:
                args = self.initialize()

                if args[0] in django_allowed_commands:
                    command = management.load_command_class('django.core', args[0])
                else:
                    command = settings.MANAGER.index.find_command(args)

                if settings.INIT_PROFILE:
                    init_profiler.disable()

                if settings.COMMAND_PROFILE:
                    command_profiler.enable()

                if isinstance(command, migrate.Command):
                    command.run_from_argv = self.exclusive_wrapper(command.run_from_argv, 'system_migrate')

                command.run_from_argv(self.argv)
                self.exit(0)

            except KeyboardInterrupt:
                self.print(
                    '> ' + self.error_color('User aborted'),
                    stream = sys.stderr
                )
            except Exception as error:
                self.handle_error(error)

            self.exit(1)
        finally:
            connection.close()

            if settings.INIT_PROFILE:
                init_profiler.dump_stats(self.get_profiler_path('init'))

            if settings.COMMAND_PROFILE:
                command_profiler.disable()
                command_profiler.dump_stats(self.get_profiler_path('command'))


    def install(self):
        try:
            django.setup()

            from systems.commands import action
            command = action.primary('install')

            settings.MANAGER.install_scripts(command, True)
            settings.MANAGER.install_requirements(command, True)
            self.exit(0)

        except KeyboardInterrupt:
            self.print(
                '> ' + self.error_color('User aborted'),
                stream = sys.stderr
            )
        except Exception as error:
            self.handle_error(error)

        self.exit(1)


    def get_profiler_path(self, name):
        from utility.environment import Environment
        base_path = os.path.join(settings.PROFILER_PATH, Environment.get_active_env())
        pathlib.Path(base_path).mkdir(parents = True, exist_ok = True)
        return os.path.join(base_path, "{}.profile".format(name))


def execute(argv):
    CLI(argv).execute()

def install():
    CLI().install()
