from collections import OrderedDict, defaultdict
from difflib import get_close_matches

from django.conf import settings
from django.core import management
from django.core.management import ManagementUtility, find_commands, load_command_class, call_command
from django.core.management.color import color_style, no_style
from django.core.management.base import BaseCommand, CommandError, CommandParser

from utility.config import RuntimeConfig
from utility.colors import ColorMixin
from utility.text import wrap
from utility.display import print_exception_info

import django
import os
import sys
import functools


@functools.lru_cache(maxsize=None)
def get_commands():
    init_commands = management.get_commands()
    include_commands = {
        'django.core': [
            'check',
            'shell',
            'dbshell',
            'inspectdb',
            'showmigrations',
            'makemigrations',
            'migrate'
        ],
        'django.contrib.contenttypes': [],
        'rest_framework': [],
        'utility': [
            'clear_locks'
        ]
    }
    commands = {}
    
    for command, namespace in init_commands.items():
        if namespace not in include_commands or command in include_commands[namespace]:
            commands[command] = namespace

    return commands


class AppManagementUtility(ColorMixin, ManagementUtility):

    def main_help_text(self):
        from .base import AppBaseCommand
        from .types.router import RouterCommand

        commands = {}
        usage = [
            "Type '{}' for help on a specific subcommand.".format(
                self.success_color("{} help <subcommand> ...".format(settings.APP_NAME))
            ),
            "",
            "Available subcommands:",
            ""
        ]

        def process_subcommands(name, command, usage, width, init_indent, indent):
            if isinstance(command, RouterCommand):
                for info in command.get_subcommands():
                    full_name = "{} {}".format(name, info[0])
                    subcommand = command.subcommands[info[0]]
                    usage.extend(wrap(
                        subcommand.get_description(True), width,
                        init_indent = "{:{width}}{}  -  ".format(' ', self.success_color(full_name), width = init_indent),
                        init_style = self.style.WARNING,
                        indent      = "".ljust(indent)
                    ))                    
                    process_subcommands(full_name, subcommand, usage, width - 5, init_indent + 5, indent + 5)

        for name, app in get_commands().items():
            if app != 'django.core':
                command = self.fetch_command(name)

                if isinstance(command, AppBaseCommand):
                    priority = command.get_priority()

                    if priority not in commands:
                        commands[priority] = {}

                    command_help = wrap(
                        command.get_description(True), settings.DISPLAY_WIDTH,
                        init_indent = " {}  -  ".format(self.success_color(name)),
                        init_style = self.style.WARNING,
                        indent      = " {:5}".format(' ')
                    )
                    process_subcommands(name, command, command_help, settings.DISPLAY_WIDTH - 5, 6, 11)
                    commands[priority][name] = command_help

        for priority in sorted(commands.keys(), reverse=True):
            for name, command_help in commands[priority].items():
                usage.extend(command_help)
        
        return '\n'.join(usage)


    def fetch_command(self, subcommand):
        commands = get_commands()
        try:
            app_name = commands[subcommand]
        except KeyError:
            subcommand = 'task'
            app_name = commands[subcommand]
        
        return load_command_class(app_name, subcommand)


    def fetch_command_tree(self):
        from .base import AppBaseCommand
        from .types.router import RouterCommand
  
        command_tree = {}

        def fetch_subcommands(command_tree, base_command):
            command = command_tree['cls']

            if isinstance(command, RouterCommand):
                for info in command.get_subcommands():
                    name = info[0]
                    full_name = "{} {}".format(base_command, name).strip()

                    command_tree['sub'][name] = {
                        'name': full_name,
                        'cls': command.subcommands[name],
                        'sub': {} 
                    }                    
                    fetch_subcommands(command_tree['sub'][name], full_name)

        for name, app in get_commands().items():
            if app != 'django.core':
                command = self.fetch_command(name)

                if isinstance(command, AppBaseCommand):
                    command_tree[name] = {
                        'name': name,
                        'cls': command,
                        'sub': {} 
                    }
                    fetch_subcommands(command_tree[name], name)

        return command_tree


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

        parser = CommandParser(add_help=False, allow_abbrev=False)
        parser.add_argument('args', nargs='*')
        namespace, extra = parser.parse_known_args(argv[1:])
        args = namespace.args
        
        if '--version' in extra:
            args = ['version']
        if not args:
            args = ['help']
        
        if '--debug' in extra:
            RuntimeConfig.debug(True)
            
        if '--no-color' in extra:
            RuntimeConfig.color(False)
        
        self.set_color_style()
        return (args.pop(0), args)


    def execute(self):
        command, args = self.initialize(self.argv)
        if command == 'help':
            if not args:
                sys.stdout.write(self.main_help_text() + '\n')
            else:
                self.fetch_command(args[0]).print_help(settings.APP_NAME, args)
        else:
            self.fetch_command(command).run_from_argv(self.argv)


def execute_from_command_line(argv = None):
    RuntimeConfig.api(False)
    try:
        sys.stdout.write('\n')
        AppManagementUtility(argv).execute()
        sys.stdout.write('\n')
        sys.exit(0)

    except Exception as e:
        if not isinstance(e, CommandError):
            style = color_style() if RuntimeConfig.color() else no_style()
            
            sys.stderr.write(style.ERROR("({}) - {}".format(type(e).__name__, str(e))) + '\n')
            if RuntimeConfig.debug():
                print_exception_info()
        
        sys.stdout.write('\n')
        sys.exit(1)
