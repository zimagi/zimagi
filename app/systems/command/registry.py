from django.conf import settings
from django.core import management
from django.core.management import load_command_class
from django.core.management.base import BaseCommand

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


class CommandRegistry(object):

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        if not getattr(self, '_initialized', False):
            self._initialized = True


    def fetch_command(self, subcommand):
        commands = get_commands()
        try:
            app_name = commands[subcommand]
        except KeyError:
            subcommand = 'task'
            app_name = commands[subcommand]

        return load_command_class(app_name, subcommand)


    def import_projects(self):
        from .types.action import ActionCommand
        command = ActionCommand()
        command.ensure_resources()
        core = command.get_instance(command._project, settings.CORE_PROJECT)
        core.provider.import_projects()


    def fetch_command_tree(self, import_projects = False):
        from .base import AppBaseCommand
        from .types.router import RouterCommand

        command_tree = {}

        if import_projects:
            self.import_projects()

        def fetch_subcommands(command_tree, base_command):
            command = command_tree['instance']

            if isinstance(command, RouterCommand):
                for info in command.get_subcommands():
                    name = info[0]
                    full_name = "{} {}".format(base_command, name).strip()

                    command_tree['sub'][name] = {
                        'name': full_name,
                        'instance': command.subcommands[name],
                        'sub': {}
                    }
                    fetch_subcommands(command_tree['sub'][name], full_name)

        for name, app in get_commands().items():
            if app != 'django.core':
                command = self.fetch_command(name)

                if isinstance(command, AppBaseCommand):
                    command_tree[name] = {
                        'name': name,
                        'instance': command,
                        'sub': {}
                    }
                    fetch_subcommands(command_tree[name], name)

        return command_tree
