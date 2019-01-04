from collections import OrderedDict, defaultdict
from difflib import get_close_matches

from django.conf import settings
from django.core import management
from django.core.management import ManagementUtility, find_commands, load_command_class
from django.core.management.color import color_style
from django.core.management.base import (
    BaseCommand, CommandError, CommandParser
)

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
        'django.contrib.auth': [],
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


class AppManagementUtility(ManagementUtility):

    def main_help_text(self):
        from .base import AppBaseCommand
        from .types.router import RouterCommand

        style = color_style()

        commands = {}
        usage = [
            "",
            "Type '{}' for help on a specific subcommand.".format(
                style.SUCCESS("{} help <subcommand> ...".format(settings.APP_NAME))
            ),
            "",
            "available subcommands:",
            ""
        ]

        def process_subcommands(name, command, usage, width, init_indent, indent):
            if isinstance(command, RouterCommand):
                for info in command.get_subcommands():
                    full_name = "{} {}".format(name, info[0])
                    subcommand = command.subcommands[info[0]]
                    usage.extend(wrap(
                        subcommand.get_description(True), width,
                        init_indent = "{:{width}}{}  -  ".format(' ', style.SUCCESS(full_name), width = init_indent),
                        init_style = style.WARNING,
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
                        init_indent = " {}  -  ".format(style.SUCCESS(name)),
                        init_style = style.WARNING,
                        indent      = " {:5}".format(' ')
                    )
                    process_subcommands(name, command, command_help, settings.DISPLAY_WIDTH - 5, 6, 11)
                    commands[priority][name] = command_help

        for priority in sorted(commands.keys(), reverse=True):
            for name, command_help in commands[priority].items():
                usage.extend(command_help)
        
        return '\n'.join(usage)


    def fetch_command_class(self, app_name, subcommand):
        if isinstance(app_name, BaseCommand):
            return app_name
        
        return load_command_class(app_name, subcommand)
     

    def fetch_command(self, subcommand):
        style = color_style()
        commands = get_commands()
        
        try:
            app_name = commands[subcommand]
        except KeyError:
            if os.environ.get('DJANGO_SETTINGS_MODULE'):
                settings.INSTALLED_APPS
            else:
                sys.stderr.write("No Django settings specified.\n")
             
            possible_matches = get_close_matches(subcommand, commands)
            sys.stderr.write(style.ERROR("Unknown command: {}".format(subcommand)))
             
            if possible_matches:
                sys.stderr.write(". Did you mean {}?".format(possible_matches[0]))
             
            sys.stderr.write("\nType '{}' for usage.\n".format(style.SUCCESS("{} help".format(settings.APP_NAME))))
            sys.exit(1)

        return self.fetch_command_class(app_name, subcommand)


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


    def execute(self):
        try:
            subcommand = self.argv[1]
        except IndexError:
            subcommand = 'help'

        parser = CommandParser(usage='%(prog)s subcommand [options] [args]', add_help=False, allow_abbrev=False)
        parser.add_argument('args', nargs='*')
        try:
            options, args = parser.parse_known_args(self.argv[2:])
        except CommandError:
            pass

        try:
            settings.INSTALLED_APPS
        except ImproperlyConfigured as exc:
            self.settings_exception = exc
        except ImportError as exc:
            self.settings_exception = exc

        if settings.configured:
            django.setup()

        if subcommand == 'help':
            if not options.args:
                sys.stdout.write(self.main_help_text() + '\n')
            else:
                self.fetch_command(options.args[0]).print_help(settings.APP_NAME, options.args)
        
        elif subcommand == 'version' or self.argv[1:] == ['--version']:
            self.fetch_command('version').run_from_argv(self.argv)
        elif self.argv[1:] in (['--help'], ['-h']):
            sys.stdout.write(self.main_help_text() + '\n')
        else:
            self.fetch_command(subcommand).run_from_argv(self.argv)


def execute_from_command_line(argv = None):
    settings.API_EXEC = False

    try:
        utility = AppManagementUtility(argv)
        utility.execute()

    except Exception as e:
        if not isinstance(e, CommandError):
            print(color_style().ERROR("({}) - {}".format(type(e).__name__, str(e))))
            print_exception_info()
        
        sys.exit(1)
 
    sys.exit(0)
