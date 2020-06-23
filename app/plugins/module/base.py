from django.conf import settings

from systems.plugins.index import BasePlugin
from systems.commands import profile
from utility.runtime import Runtime
from utility.data import ensure_list, deep_merge

import os
import re
import pathlib
import yaml
import glob
import copy


class BaseProvider(BasePlugin('module')):

    def __init__(self, type, name, command, instance = None):
        super().__init__(type, name, command, instance)
        self._module_config = None


    def initialize_instance(self, instance, created):
        if created and instance.name is None:
            instance.name = self.get_module_name(instance)

    def prepare_instance(self, instance, created):
        if instance.name != 'core':
            self.manager.index.save_module_config(instance.name, {
                'remote': instance.remote,
                'reference': instance.reference
            })


    def get_module_name(self, instance):
        return instance.id


    @property
    def base_path(self):
        env = self.command.get_env()
        return os.path.join(settings.MODULE_BASE_PATH, env.name)

    def module_path(self, name, ensure = True):
        path = os.path.join(self.base_path, name)
        if ensure:
            pathlib.Path(path).mkdir(parents = True, exist_ok = True)
        return path

    def module_config(self, force = False):
        if not self._module_config or force:
            self._module_config = self.load_yaml('zimagi.yml')
        return self._module_config

    def load_parents(self):
        config = self.module_config()
        if config and 'modules' in config:
            for fields in ensure_list(config['modules']):
                fields = copy.deepcopy(fields)
                remote = fields.pop('remote')
                provider = fields.pop('provider', 'git')
                self.command.exec_local('module add', {
                    'module_provider_name': provider,
                    'remote': remote,
                    'module_fields': fields,
                    'verbosity': 0
                })
                modules = list(self.command.search_instances(self.command._module,
                    "remote={}".format(remote)
                ))
                modules[0].provider.load_parents()


    def get_profile_class(self):
        return profile.CommandProfile

    def get_profile(self, profile_name, show_options = True):
        instance = self.check_instance('module get profile')
        config = self.module_config()

        if config is None or not isinstance(config, dict):
            config = {}

        config.setdefault('profiles', 'profiles')
        module_path = self.module_path(instance.name)
        profile_data = None
        profile_names = []

        if config['profiles']:
            base_path = "{}/{}".format(module_path, config['profiles'])
            for file in glob.glob("{}/**/*.yml".format(base_path), recursive = True):
                profile_names.append(re.sub(r'^\/([^\.]+)\.yml$', r'\1', file[len(base_path):]))

            if not profile_data:
                profile_data = self.load_yaml("{}/{}.yml".format(config['profiles'], profile_name))

        if profile_name == 'list' or profile_data is None:
            if show_options:
                self.command.info("Available profiles in this module:\n")
                for name in sorted(profile_names):
                    self.command.info(" * {}".format(self.command.header_color(name)))

                if profile_name == 'list':
                    self.command.error('')
                else:
                    self.command.error("Profile {} not found in module {}".format(profile_name, self.instance.name))
            else:
                return None

        return self.get_profile_class()(self, profile_name, profile_data)

    def run_profile(self, profile_name, config = None, components = None, display_only = False, plan = False, ignore_missing = False):
        if not config:
            config = {}
        if not components:
            components = []

        self.check_instance('module run profile')
        profile = self.get_profile(profile_name, show_options = not ignore_missing)
        if profile:
            profile.run(components, config = config, display_only = display_only, plan = plan)

    def export_profile(self, components = None):
        if not components:
            components = []

        self.check_instance('module export profile')
        profile = self.get_profile_class()(self)
        self.command.info(yaml.dump(profile.export(components)))

    def destroy_profile(self, profile_name, config = None, components = None, display_only = False, ignore_missing = False):
        if not config:
            config = {}
        if not components:
            components = []

        self.check_instance('module destroy profile')
        profile = self.get_profile(profile_name, show_options = not ignore_missing)
        if profile:
            profile.destroy(components, config = config, display_only = display_only)


    def import_tasks(self, tasks_path):
        tasks = {}
        for file_name in self.get_file_names(tasks_path, 'yml'):
            task_file = os.path.join(tasks_path, file_name)
            for name, config in self.load_yaml(task_file).items():
                if not name.startswith('_'):
                    tasks[name] = config
        return tasks

    def get_task(self, task_name, show_options = True):
        instance = self.check_instance('module get task')
        module_config = self.module_config()
        tasks = {}

        module_config.setdefault('tasks', 'tasks')

        if module_config['tasks']:
            module_path = self.module_path(instance.name)
            tasks_path = os.path.join(module_path, module_config['tasks'])
            tasks = self.import_tasks(tasks_path)

        if task_name == 'list' or task_name not in tasks:
            if show_options:
                self.command.info("Available tasks in this module:\n")
                for name in sorted(tasks.keys()):
                    task = self.command.get_provider(
                        'task', tasks[name]['provider'], self, tasks[name]
                    )
                    fields = deep_merge(task.get_fields(), { 'provider': '<required>' })
                    self.command.info(" * {}\n".format(self.command.header_color(name)))
                    self.command.notice(yaml.dump(deep_merge(fields, tasks[name])))

            if task_name == 'list':
                self.command.error('')
            else:
                self.command.error("Task {} not found in module {} zimagi.yml".format(task_name, self.instance.name))

        config = tasks[task_name]
        provider = config.pop('provider', 'command')

        return self.command.get_provider(
            'task', provider, self, config
        )

    def exec_task(self, task_name, params = None):
        if not params:
            params = {}

        task = self.get_task(task_name)
        task.exec(params)


    def get_file_names(self, base_path, *extensions):
        files = []
        for filename in os.listdir(base_path):
            if extensions:
                for ext in extensions:
                    if filename.endswith(".{}".format(ext)):
                        files.append(filename)
            else:
                files.append(filename)
        return files

    def load_file(self, file_name, binary = False, instance = None):
        if not instance:
            instance = self.check_instance('module load file')

        module_path = self.module_path(instance.name)
        path = os.path.join(module_path, file_name)
        operation = 'rb' if binary else 'r'
        content = None

        if os.path.exists(path):
            with open(path, operation) as file:
                content = file.read()

        return content

    def load_yaml(self, file_name, instance = None):
        content = self.load_file(file_name, instance)
        if content:
            content = yaml.safe_load(content)
        return content


    def save_file(self, file_name, content = '', binary = False, instance = None):
        if not instance:
            instance = self.check_instance('module save file')

        module_path = self.module_path(instance.name)
        path = os.path.join(module_path, file_name)
        operation = 'wb' if binary else 'w'

        pathlib.Path(path).mkdir(parents = True, exist_ok = True)

        with open(path, operation) as file:
            file.write(content)

        return content

    def save_yaml(self, file_name, data = None):
        if not data:
            data = {}

        return self.save_file(file_name, yaml.dump(data))
