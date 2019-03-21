from collections import OrderedDict

from django.utils.module_loading import import_string

from utility.data import ensure_list
from utility.shell import Shell

import os
import sys
import re
import pathlib
import importlib
import json
import yaml


class RequirementError(Exception):
    pass


class Config(object):

    @classmethod
    def value(cls, name, default = None):
        # Order of precedence
        # 1. Local environment variable if it exists
        # 2. Default value provided

        value = default

        # Check for an existing environment variable
        try:
            value = os.environ[name]
        except:
            pass

        return value

    @classmethod
    def boolean(cls, name, default = False):
        return json.loads(cls.value(name, str(default)).lower())

    @classmethod
    def integer(cls, name, default = 0):
        return int(cls.value(name, default))

    @classmethod
    def decimal(cls, name, default = 0):
        return float(cls.value(name, default))

    @classmethod
    def string(cls, name, default = ''):
        return str(cls.value(name, default))

    @classmethod
    def list(cls, name, default = []):
        if not cls.value(name, None):
            return default
        return [x.strip() for x in cls.string(name).split(',')]

    @classmethod
    def dict(cls, name, default = {}):
        value = cls.value(name, default)

        if isinstance(value, str):
            value = json.loads(value)

        return value


    @classmethod
    def load(cls, path, default = {}):
        data = default

        if os.path.exists(path):
            with open(path, 'r') as file:
                data = {}
                for statement in file.read().split("\n"):
                    statement = statement.strip()

                    if statement and statement[0] != '#':
                        (variable, value) = statement.split("=")
                        data[variable] = value
        return data

    @classmethod
    def save(cls, path, data):
        with open(path, 'w') as file:
            statements = []
            for variable, value in data.items():
                statements.append("{}={}".format(variable.upper(), value))

            file.write("\n".join(statements))

    @classmethod
    def variable(cls, scope, name):
        return "{}_{}".format(scope.upper(), name.upper())


class Loader(object):

    def __init__(self, app_dir, data_dir, runtime_path, module_base_dir, default_env):
        self.app_dir = app_dir
        self.data_dir = data_dir
        self.config = Config.load(runtime_path, {})
        self.env = self.config.get('CENV_ENV', default_env)
        self.module_dir = os.path.join(module_base_dir, self.env)
        self.modules = {}
        self.ordered_modules = None
        self.plugins = {}
        self.reload()

    def reload(self):
        pathlib.Path(self.module_dir).mkdir(mode = 0o700, parents = True, exist_ok = True)

        self.module_config(self.app_dir)
        self.update_search_path()
        self.load_plugins()


    def load_file(self, file_path):
        content = None
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
        return content

    def load_yaml(self, file_path):
        content = self.load_file(file_path)
        if content:
            content = yaml.load(content)
        return content


    def module_config(self, path):
        if path not in self.modules:
            cenv_file = os.path.join(path, 'cenv.yml')
            self.modules[path] = self.load_yaml(cenv_file)
        return self.modules[path]

    def module_lib_dir(self, path):
        config = self.module_config(path)
        lib_dir = False

        if 'lib' in config:
            lib_dir = config['lib']
            if not lib_dir:
                return False
            elif lib_dir == '.':
                lib_dir = False

        return os.path.join(path, lib_dir) if lib_dir else path

    def get_modules(self):
        if not self.ordered_modules:
            self.ordered_modules = OrderedDict()
            self.ordered_modules[self.app_dir] = self.module_config(self.app_dir)

            modules = {}
            for name in os.listdir(self.module_dir):
                path = os.path.join(self.module_dir, name)
                if os.path.isdir(path):
                    modules[name] = self.module_config(path)

            def process(name, config):
                if 'modules' in config:
                    for parent in config['modules'].keys():
                        if parent in modules:
                            process(parent, modules[parent])

                path = os.path.join(self.module_dir, name)
                self.ordered_modules[path] = config

            for name, config in modules.items():
                process(name, config)

        return self.ordered_modules

    def get_module_libs(self, include_core = True):
        module_libs = OrderedDict()
        for path, config in self.get_modules().items():
            if include_core or path != self.app_dir:
                lib_dir = self.module_lib_dir(path)
                if lib_dir:
                    module_libs[lib_dir] = config
        return module_libs


    def update_search_path(self):
        for lib_dir in self.get_module_libs().keys():
            sys.path.append(lib_dir)
        importlib.invalidate_caches()


    def module_dirs(self, sub_dir = None, include_core = True):
        module_dirs = []
        for lib_dir in self.get_module_libs(include_core).keys():
            if sub_dir:
                abs_sub_dir = os.path.join(lib_dir, sub_dir)
                if os.path.isdir(abs_sub_dir):
                    module_dirs.append(abs_sub_dir)
            else:
                module_dirs.append(lib_dir)
        return module_dirs

    def module_file(self, *path_components):
        module_file = None

        for module_dir in self.module_dirs():
            path = os.path.join(module_dir, *path_components)
            if os.path.isfile(path):
                module_file = path

        if not module_file:
            raise RequirementError("Module file {} not found".format("/".join(path_components)))
        return module_file

    def help_search_path(self):
        return self.module_dirs('help')

    def settings_modules(self):
        modules = []
        for settings_dir in self.module_dirs('settings', False):
            for name in os.listdir(settings_dir):
                if name[0] != '_':
                    module = "settings.{}".format(name.replace('.py', ''))
                    modules.append(importlib.import_module(module))
        return modules


    def installed_apps(self):
        apps = []
        for module_dir in self.module_dirs():
            data_dir = os.path.join(module_dir, 'data')
            interface_dir = os.path.join(module_dir, 'interface')

            if os.path.isdir(interface_dir):
                for name in os.listdir(interface_dir):
                    if name[0] != '_':
                        apps.append("interface.{}".format(name))

            if os.path.isdir(data_dir):
                for name in os.listdir(data_dir):
                    if name[0] != '_':
                        apps.append("data.{}".format(name))
        return apps

    def installed_middleware(self):
        middleware = []
        for middleware_dir in self.module_dirs('middleware'):
            for name in os.listdir(middleware_dir):
                if name[0] != '_':
                    middleware.append("middleware.{}.Middleware".format(name))
        return middleware


    def parse_requirements(self):
        requirements = []
        for path, config in self.get_modules().items():
            if 'requirements' in config:
                for requirement_path in ensure_list(config['requirements']):
                    requirement_path = os.path.join(path, requirement_path)
                    file_contents = self.load_file(requirement_path)
                    if file_contents:
                        requirements.extend([ req for req in file_contents.split("\n") if req and req[0].strip() != '#' ])
        return requirements

    def install_requirements(self):
        req_map = {}
        for req in self.parse_requirements():
            # PEP 508
            req_map[re.split(r'[\>\<\!\=\~\s]+', req)[0]] = req

        requirements = list(req_map.values())

        if len(requirements):
            if not Shell.exec(['pip3', 'install'] + requirements, display = False):
                raise RequirementError("Installation of requirements failed: {}".format("\n".join(requirements)))


    def load_plugins(self):
        self.plugins = {}
        for plugin_dir in self.module_dirs('plugins'):
            for type in os.listdir(plugin_dir):
                if type[0] != '_':
                    provider_dir = os.path.join(plugin_dir, type)
                    base_module = "plugins.{}".format(type)
                    base_class = "{}.base.BaseProvider".format(base_module)

                    if type not in self.plugins:
                        self.plugins[type] = {
                            'base': base_class,
                            'providers': {}
                        }
                    for name in os.listdir(provider_dir):
                        if name[0] != '_' and name != 'base.py' and name.endswith('.py'):
                            name = name.strip('.py')
                            provider_class = "{}.{}.Provider".format(base_module, name)
                            self.plugins[type]['providers'][name] = provider_class

    def provider_base(self, type):
        return self.plugins[type]['base']

    def providers(self, type, include_system = False):
        providers = {}
        for name, class_name in self.plugins[type]['providers'].items():
            if include_system or not name.startswith('sys_'):
                providers[name] = class_name
        return providers


    def load_roles(self):
        roles = {}
        for path, config in self.get_modules().items():
            if 'roles' in config:
                for name, description in config['roles'].items():
                    roles[name] = description
        return roles


    def load_config_provisioner(self, profile):
        return import_string("provisioners.config.Provisioner")(
            'config',
            profile
        )

    def load_provisioners(self, profile):
        provisioners = {}
        for provisioner_dir in self.module_dirs('provisioners'):
            for type in os.listdir(provisioner_dir):
                if type[0] != '_' and type.endswith('.py'):
                    name = type.replace('.py', '')

                    if name != 'config':
                        provisioner_class = "provisioners.{}.Provisioner".format(name)
                        instance = import_string(provisioner_class)(name, profile)
                        priority = instance.priority()

                        if priority not in provisioners:
                            provisioners[priority] = [ instance ]
                        else:
                            provisioners[priority].append(instance)
        return provisioners


    def service_file(self, name):
        directory = os.path.join(self.data_dir, 'run')
        pathlib.Path(directory).mkdir(mode = 0o700, parents = True, exist_ok = True)
        return os.path.join(directory, "{}.data".format(name))

    def save_service(self, name, id, data = {}):
        data['id'] = id
        with open(self.service_file(name), 'w') as file:
            file.write(json.dumps(data))

    def get_service(self, name):
        service_file = self.service_file(name)
        if os.path.isfile(service_file):
            with open(self.service_file(name), 'r') as file:
                return json.loads(file.read())
        return None

    def delete_service(self, name):
        os.remove(self.service_file(name))
