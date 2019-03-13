from importlib import import_module

from django.conf import settings
from django.apps import apps, AppConfig
from django.core import management
from django.core.management.base import BaseCommand

import os
import pkgutil
import functools


def find_commands(command_dir):
    return [
        name for _, name, is_pkg in pkgutil.iter_modules([ command_dir ])
        if not is_pkg and not name.startswith('_')
    ]

@functools.lru_cache(maxsize=None)
def get_commands():
    commands = management.get_commands()
    index = {}
    included = (
        'check',
        'shell',
        'dbshell',
        'inspectdb',
        'showmigrations',
        'makemigrations',
        'migrate'
    )
    for command, namespace in commands.items():
        if command in included:
            index[command] = namespace

    if settings.configured:
        for app_config in reversed(list(apps.get_app_configs())):
            if type(app_config) is AppConfig and app_config.name.startswith('interface.'):
                index.update({
                    name: app_config.name for name in find_commands(app_config.path)
                })
    return index


def load_command_class(app_name, name):
    module = import_module("{}.{}".format(app_name, name))
    return module.Command()


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


    def load_projects(self):
        from .types.action import ActionCommand
        command = ActionCommand()
        command.ensure_resources()

        for project in command.get_instances(command._project):
            project.provider.load_parents()


    def fetch_command_tree(self, load_projects = False):
        from .base import AppBaseCommand
        from .types.router import RouterCommand

        command_tree = {}

        if load_projects:
            self.load_projects()

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
