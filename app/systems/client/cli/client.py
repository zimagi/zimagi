import cProfile
import os
import sys

from django.conf import settings
from django.core.management.base import CommandError, CommandParser
from utility.display import format_exception_info
from utility.terminal import TerminalMixin

from .errors import CommandNotFoundError
from .index import CommandIndex


class Client(TerminalMixin):
    def __init__(self, argv=None):
        super().__init__()
        self.argv = argv if argv else []

    def handle_error(self, error):
        if isinstance(error, CommandError):
            self.print("** " + self.error_color(error), sys.stderr)
            if settings.DEBUG:
                self.print(
                    "> " + self.traceback_color("\n".join([item.strip() for item in format_exception_info()])),
                    stream=sys.stderr,
                )

    def initialize(self):
        parser = CommandParser(add_help=False, allow_abbrev=False)
        parser.add_argument("args", nargs="*")
        namespace, extra = parser.parse_known_args(self.argv[1:])
        args = namespace.args

        if not args:
            args = ["help"]

        if "--debug" in extra:
            settings.DEBUG = True

        if "--no-color" in extra:
            settings.DISPLAY_COLOR = False

        return args

    def execute(self):
        try:
            if settings.COMMAND_PROFILE:
                command_profiler = cProfile.Profile()

            if settings.INIT_PROFILE:
                init_profiler = cProfile.Profile()
                init_profiler.enable()

            try:
                args = self.initialize()
                command = CommandIndex().find(args)

                if settings.INIT_PROFILE:
                    init_profiler.disable()

                if settings.COMMAND_PROFILE:
                    command_profiler.enable()

                if not command:
                    command_name = " ".join(args)
                    raise CommandNotFoundError(f"Command {command_name} not found")

                command.exec(self.argv)
                self.exit(0)

            except KeyboardInterrupt:
                self.print("> " + self.error_color("User aborted"), stream=sys.stderr)
            except Exception as error:
                self.handle_error(error)

            self.exit(1)
        finally:
            if settings.INIT_PROFILE:
                init_profiler.dump_stats(self.get_profiler_path("init"))

            if settings.COMMAND_PROFILE:
                command_profiler.disable()
                command_profiler.dump_stats(self.get_profiler_path("command"))

    def get_profiler_path(self, name):
        return os.path.join(settings.PROFILE_DIR, f"{name}.profile")


def execute(argv):
    Client(argv).execute()
