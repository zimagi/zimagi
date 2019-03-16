from utility.data import ensure_list
from utility.shell import Shell

import os
import sys
import re
import importlib
import json
import yaml


class RequirementError(Exception):
    pass


class Loader(object):

    def __init__(self, app_dir, runtime_dir, project_base_dir, default_env):
        self.app_dir = app_dir
        self.config = Config.load(runtime_dir, {})
        self.env = self.config.get('CENV_ENV', default_env)
        self.project_dir = os.path.join(project_base_dir, self.env)
        self.projects = {}
        self.plugins = {}

        self.project_config(app_dir)
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


    def project_config(self, path):
        if path not in self.projects:
            cenv_file = os.path.join(path, 'cenv.yml')
            self.projects[path] = self.load_yaml(cenv_file)
        return self.projects[path]

    def project_lib_dir(self, path):
        config = self.project_config(path)
        lib_dir = False

        if 'lib' in config:
            lib_dir = config['lib']
            if lib_dir != '.':
                lib_dir = os.path.join(path, lib_dir)
            else:
                lib_dir = path

        return lib_dir

    def update_search_path(self):
        for name in os.listdir(self.project_dir):
            path = os.path.join(self.project_dir, name)

            if os.path.isdir(path):
                lib_dir = self.project_lib_dir(path)
                if lib_dir:
                    sys.path.append(lib_dir)

        importlib.invalidate_caches()


    def project_dirs(self, sub_dir = None, include_core = True):
        project_dirs = []
        for path, config in self.projects.items():
            if include_core or path != self.app_dir:
                lib_dir = self.project_lib_dir(path)
                if lib_dir:
                    if sub_dir:
                        sub_dir = os.path.join(lib_dir, sub_dir)
                        if os.path.isdir(sub_dir):
                            project_dirs.append(sub_dir)
                    else:
                        project_dirs.append(lib_dir)
        return project_dirs

    def help_search_path(self):
        return self.project_dirs('help')

    def settings_modules(self):
        modules = []
        for settings_dir in self.project_dirs('settings', False):
            for name in os.listdir(settings_dir):
                if name[0] != '_':
                    module = "settings.{}".format(name.replace('.py', ''))
                    modules.append(importlib.import_module(module))
        return modules


    def installed_apps(self):
        apps = []
        for project_dir in self.project_dirs():
            data_dir = os.path.join(project_dir, 'data')
            interface_dir = os.path.join(project_dir, 'interface')

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
        for middleware_dir in self.project_dirs('middleware'):
            for name in os.listdir(middleware_dir):
                if name[0] != '_':
                    middleware.append("middleware.{}.Middleware".format(name))
        return middleware


    def parse_requirements(self):
        requirements = []
        for path, config in self.projects.items():
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
        for plugin_dir in self.project_dirs('plugins'):
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
