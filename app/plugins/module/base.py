from django.conf import settings

from systems.plugins import data
from systems.provisioner import profile
from utility.data import ensure_list

import os
import re
import pathlib
import yaml


class BaseProvider(data.DataCommandProvider):

    def __init__(self, type, name, command, instance = None):
        super().__init__(type, name, command, instance)
        self._module_config = None

    @property
    def facade(self):
        return self.command._module


    def module_path(self, name, ensure = True):
        env = self.command.get_env()
        path = os.path.join(settings.MODULE_BASE_PATH, env.name, name)
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
        return profile.ModuleProfile

    def get_profile(self, profile_name):
        config = self.module_config()
        config.setdefault('profiles', [])
        profile_data = None

        for profile_dir in ensure_list(config['profiles']):
            profile_data = self.load_yaml("{}/{}.yml".format(profile_dir, profile_name))

        if profile_data is None:
            self.command.error("Profile {} not found in module {}".format(profile_name, self.instance.name))

        return self.get_profile_class()(self, profile_data)

    def provision_profile(self, profile_name, components = []):
        self.check_instance('module provision profile')
        profile = self.get_profile(profile_name)
        profile.provision(components)

    def export_profile(self, components = []):
        self.check_instance('module export profile')
        profile = self.get_profile_class()(self)
        self.command.info(yaml.dump(profile.export(components), default_flow_style=False))

    def destroy_profile(self, profile_name, components = []):
        self.check_instance('module destroy profile')
        profile = self.get_profile(profile_name)
        profile.destroy(components)


    def get_task(self, task_name):
        config = self.module_config()
        config.setdefault('tasks', {})

        if task_name not in config['tasks']:
            self.command.error("Task {} not found in module {} cenv.yml".format(task_name, self.instance.name))

        task = config['tasks'][task_name]
        provider = task.pop('provider')

        return self.command.get_provider(
            'task', provider, self, task
        )

    def exec_task(self, task_name, servers, params = {}):
        instance = self.check_instance('module exec task')
        task = self.get_task(task_name)

        if task.check_access():
            task.exec(servers, params)
        else:
            self.command.error("Access is denied for task {}".format(task_name))


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
            content = yaml.load(content)
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
        return self.save_file(file_name, yaml.dump(data, default_flow_style=False))
