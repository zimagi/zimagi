from django.conf import settings
from django.db import connection
from django.core import management
from django.core.management import call_command
from django.core.management.base import CommandError, CommandParser

from utility.runtime import Runtime
from utility.environment import Environment
from utility.terminal import TerminalMixin
from utility.display import format_exception_info

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

    def __init__(self, argv):
        super().__init__()
        self.argv = argv


    def handle_error(self, error):
        if not isinstance(error, CommandError):
            self.print('** ' + self.error_color(error.args[0]), sys.stderr)
            if Runtime.debug():
                self.print('> ' + self.traceback_color(
                        "\n".join([ item.strip() for item in format_exception_info() ])
                    ),
                    stream = sys.stderr
                )


    def initialize(self):
        django.setup()

        parser = CommandParser(add_help = False, allow_abbrev = False)
        parser.add_argument('args', nargs = '*')
        namespace, extra = parser.parse_known_args(self.argv[1:])
        args = namespace.args

        if not args:
            args = ['help']

        if '--debug' in extra:
            Runtime.debug(True)

        if '--no-color' in extra:
            Runtime.color(False)

        if not settings.NO_MIGRATE and args and args[0] not in ('check', 'migrate', 'makemigrations'):
            verbosity = 3 if Runtime.debug() else 0
            start_time = time.time()
            current_time = start_time

            while (current_time - start_time) <= settings.AUTO_MIGRATE_TIMEOUT:
                try:
                    call_command('migrate', interactive = False, verbosity = verbosity)
                    break

                except Exception:
                    pass

                time.sleep(settings.AUTO_MIGRATE_INTERVAL)
                current_time = time.time()

        return args

    def execute(self):
        try:
            if settings.INIT_PROFILE or settings.COMMAND_PROFILE:
                Runtime.parallel(False)

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

                command.run_from_argv(self.argv)
                self.exit(0)

            except KeyboardInterrupt:
                self.print(
                    '> ' + self.error_color('User aborted'),
                    stream = sys.stderr
                )
            except Exception as e:
                self.handle_error(e)

            self.exit(1)
        finally:
            connection.close()

            if settings.INIT_PROFILE:
                init_profiler.dump_stats(self.get_profiler_path('init'))

            if settings.COMMAND_PROFILE:
                command_profiler.disable()
                command_profiler.dump_stats(self.get_profiler_path('command'))


    def get_profiler_path(self, name):
        base_path = os.path.join(settings.PROFILER_PATH, Environment.get_active_env())
        pathlib.Path(base_path).mkdir(mode = 0o700, parents = True, exist_ok = True)
        return os.path.join(base_path, "{}.profile".format(name))


def execute(argv):
    CLI(argv).execute()
