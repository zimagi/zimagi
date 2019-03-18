from django.conf import settings
from django.core.management import call_command
from django.core.management.color import color_style, no_style
from django.core.management.base import CommandError, CommandParser

from systems.command.registry import CommandRegistry
from utility.runtime import Runtime
from utility.terminal import TerminalMixin
from utility.display import format_exception_info

import django
import sys
import re


class CLI(TerminalMixin):

    def __init__(self, argv):
        super().__init__()
        self.argv = argv
        self.registry = CommandRegistry()


    def start_django(self):
        try:
            settings.INSTALLED_APPS
        except ImproperlyConfigured as exc:
            self.settings_exception = exc
        except ImportError as exc:
            self.settings_exception = exc

        if settings.configured:
            django.setup()
            call_command('migrate', interactive = False, verbosity = 0)

    def initialize(self, argv):
        self.start_django()

        parser = CommandParser(add_help = False, allow_abbrev = False)
        parser.add_argument('args', nargs = '*')
        namespace, extra = parser.parse_known_args(argv[1:])
        args = namespace.args

        if '--version' in extra:
            args = ['version']
        if not args:
            args = ['help']

        if '--debug' in extra:
            Runtime.debug(True)

        if '--no-color' in extra:
            Runtime.color(False)

        Runtime.api(False)
        return args

    def execute(self):
        command = self.registry.find_command(
            self.initialize(self.argv),
            main = True
        )
        self.print()
        command.run_from_argv(self.argv)


    def handle_error(self, error):
        if not isinstance(error, CommandError):
            self.print()
            self.print(self.error_color(" ** {}".format(str(error))),
                sys.stderr
            )
            if Runtime.debug():
                exception = "\n".join([ '  ' + item.strip() for item in format_exception_info() ])
                exception = re.sub(r'[\{\}]', '', exception)
                self.print()
                self.print(self.traceback_color(exception), stream = sys.stderr)


def execute(argv):
    cli = CLI(argv)
    try:
        cli.execute()
        cli.exit(0)
    except Exception as e:
        cli.handle_error(e)
        cli.exit(1)
