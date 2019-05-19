from django.conf import settings

from systems.plugins import data
from systems.command import profile
from utility.data import ensure_list

import os
import re
import pathlib
import yaml


class BaseProvider(data.DataPluginProvider):

    def __init__(self, type, name, command, instance = None):
        super().__init__(type, name, command, instance)
        self._module_config = None

    @property
    def facade(self):
        return self.command._module


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
            self._module_config = self.load_yaml('cenv.yml')
        return self._module_config

    def load_parents(self):
        config = self.module_config()
        if config and 'modules' in config:
            for name, fields in config['modules'].items():
                provider = fields.pop('provider', 'git')
                self.command.exec_local('module save', {
                    'module_provider_name': provider,
                    'module_name': name,
                    'module_fields': fields,
                    'verbosity': 0
                })
                module = self.command.get_instance(self.command._module, name)
                module.provider.load_parents()


    def get_profile_class(self):
        return profile.CommandProfile

    def get_profile(self, profile_name):
        config = self.module_config()
        config.setdefault('profiles', [])
        profile_data = None

        for profile_dir in ensure_list(config['profiles']):
            profile_data = self.load_yaml("{}/{}.yml".format(profile_dir, profile_name))
            if profile_data:
                break

        if profile_data is None:
            self.command.error("Profile {} not found in module {}".format(profile_name, self.instance.name))

        return self.get_profile_class()(self, profile_name, profile_data)

    def provision_profile(self, profile_name, config = {}, components = [], display_only = False, plan = False):
        self.check_instance('module provision profile')
        profile = self.get_profile(profile_name)
        profile.provision(components, config = config, display_only = display_only, plan = plan)

    def export_profile(self, components = []):
        self.check_instance('module export profile')
        profile = self.get_profile_class()(self)
        self.command.info(yaml.dump(profile.export(components)))

    def destroy_profile(self, profile_name, config = {}, components = [], display_only = False):
        self.check_instance('module destroy profile')
        profile = self.get_profile(profile_name)
        profile.destroy(components, config = config, display_only = display_only)


    def import_tasks(self, tasks_path):
        tasks = {}
        for file_name in self.get_file_names(tasks_path, 'yml'):
            task_file = os.path.join(tasks_path, file_name)
            for name, config in self.load_yaml(task_file).items():
                tasks[name] = config
        return tasks

    def get_task(self, task_name):
        instance = self.check_instance('module get task')
        module_config = self.module_config()
        tasks = {}

        if 'tasks' in module_config:
            module_path = self.module_path(instance.name)
            tasks_path = os.path.join(module_path, module_config['tasks'])
            tasks = self.import_tasks(tasks_path)

        if task_name not in tasks:
            self.command.error("Task {} not found in module {} cenv.yml".format(task_name, self.instance.name))

        config = tasks[task_name]
        provider = config.pop('provider', 'command')

        return self.command.get_provider(
            'task', provider, self, config
        )

    def exec_task(self, task_name, params = {}):
        task = self.get_task(task_name)

        if task.check_access():
            task.exec(params)
        else:
            self.command.error("Access is denied for task {}".format(task_name))


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

    def load_file(self, file_name, binary = False):
        instance = self.check_instance('module load file')
        module_path = self.module_path(instance.name)
        path = os.path.join(module_path, file_name)
        operation = 'rb' if binary else 'r'
        content = None

        if os.path.exists(path):
            with open(path, operation) as file:
                content = file.read()

        return content

    def load_yaml(self, file_name):
        content = self.load_file(file_name)
        if content:
            content = yaml.safe_load(content)
        return content


    def save_file(self, file_name, content = '', binary = False):
        instance = self.check_instance('module save file')
        module_path = self.module_path(instance.name)
        path = os.path.join(module_path, file_name)
        operation = 'wb' if binary else 'w'

        pathlib.Path(path).mkdir(parents = True, exist_ok = True)

        with open(path, operation) as file:
            file.write(content)

        return content

    def save_yaml(self, file_name, data = {}):
        return self.save_file(file_name, yaml.dump(data))
