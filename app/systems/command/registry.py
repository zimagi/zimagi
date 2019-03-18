from importlib import import_module

from django.conf import settings
from django.apps import apps, AppConfig
from django.core import management
from django.core.management.base import CommandError

from utility.runtime import Runtime

import os
import re
import copy
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
    if app_name == 'django.core':
        return management.load_command_class(app_name, name)
    return import_module("{}.{}".format(app_name, name)).Command()


class CommandRegistryError(Exception):
    pass


class CommandRegistry(object):

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        if not getattr(self, '_initialized', False):
            self._initialized = True


    def fetch_command(self, subcommand, main = False):
        app_name = get_commands()[subcommand]
        if main and app_name == 'django.core':
            Runtime.system_command(True)
        return load_command_class(app_name, subcommand)


    def fetch_command_tree(self):
        from .base import AppBaseCommand
        from .types.router import RouterCommand

        command_tree = {}

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


    def find_command(self, full_name, parent = None, main = False):
        from .types.router import RouterCommand

        command = re.split('\s+', full_name) if isinstance(full_name, str) else full_name

        def find(components, command_tree, parents = []):
            name = components.pop(0)
            parent = parents[-1] if parents else None

            if name not in command_tree:
                try:
                    return self.fetch_command(name, main)
                except Exception as e:
                    parent_names = [ x.command_name for x in parents ]
                    command_name = "{} {}".format(" ".join(parent_names), name) if parent_names else name

                    parent.print()
                    parent.print_help()
                    raise CommandRegistryError("Command '{}' not found".format(command_name), parent)

            instance = type(command_tree[name]['instance'])()
            instance.command_name = name
            instance.parent_command = parent

            if len(components) and isinstance(instance, RouterCommand):
                parents.append(instance)
                return find(components, command_tree[name]['sub'], parents)
            else:
                return instance

        command = find(
            copy.copy(list(command)),
            self.fetch_command_tree()
        )
        if parent:
            if parent.parent_messages:
                command.parent_messages = parent.parent_messages
            else:
                command.parent_messages = parent.messages

        return command
