from collections import OrderedDict
from functools import lru_cache

from settings import core as settings
from django.utils.module_loading import import_string

from systems.index import SpecificationIndex

import os
import logging


logger = logging.getLogger(__name__)


class RequirementError(Exception):
    pass


class ManagerIndexMixin(object):

    def __init__(self):
        super().__init__()
        self.index = SpecificationIndex(self)
        self.default_modules = settings.DEFAULT_MODULES
        self.roles = {}
        self.modules = {}
        self.ordered_modules = None
        self.plugins = {}
        self.models = None
        self.facade_index = None


    def load_index(self):
        self.index.load()
        self.index.print()
        exit()


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
                            if modules[parent]:
                                process(parent, modules[parent])

                path = os.path.join(self.module_dir, name)
                self.ordered_modules[path] = config

            for name, config in modules.items():
                if config:
                    process(name, config)

            logger.debug("Loading modules: {}".format(self.ordered_modules))

        return self.ordered_modules

    def get_module_libs(self, include_core = True):
        module_libs = OrderedDict()
        for path, config in self.get_modules().items():
            if include_core or path != self.app_dir:
                lib_dir = self.module_lib_dir(path)
                if lib_dir:
                    module_libs[lib_dir] = config

        logger.debug("Loading module MCMI libraries: {}".format(module_libs))
        return module_libs


    def module_config(self, path):
        if path not in self.modules:
            mcmi_file = os.path.join(path, 'mcmi.yml')
            self.modules[path] = self.load_yaml(mcmi_file)

            if self.modules[path] is None:
                self.modules[path] = {
                    'lib': '.'
                }
        return self.modules[path]

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

    def module_name(self, file):
        if file.startswith(self.app_dir):
            return settings.CORE_MODULE
        return file.replace(self.module_dir + '/', '').split('/')[0]

    def module_file(self, *path_components):
        module_file = None

        for module_dir in self.module_dirs():
            path = os.path.join(module_dir, *path_components)
            if os.path.isfile(path):
                module_file = path

        if not module_file:
            raise RequirementError("Module file {} not found".format("/".join(path_components)))
        return module_file


    def load_roles(self, reset = False):
        roles = {}

        if not self.roles or reset:
            for path, config in self.get_modules().items():
                if 'roles' in config:
                    for name, description in config['roles'].items():
                        self.roles[name] = description

            logger.debug("Application roles: {}".format(self.roles))

        return self.roles


    @lru_cache(maxsize = None)
    def get_models(self):
        from django.apps import apps
        if not self.models:
            self.models = []
            for model in apps.get_models():
                if getattr(model, 'facade', None):
                    self.models.append(model)
        return self.models

    @lru_cache(maxsize = None)
    def get_facade_index(self):
        if not self.facade_index:
            self.facade_index = {}
            for model in self.get_models():
                facade = model.facade
                self.facade_index[facade.name] = facade
        return self.facade_index


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


    def load_component(self, profile, name):
        component_class = "components.{}.ProfileComponent".format(name)
        return import_string(component_class)(name, profile)

    def load_components(self, profile):
        components = {}
        for component_dir in self.module_dirs('components'):
            for type in os.listdir(component_dir):
                if type[0] != '_' and type.endswith('.py'):
                    name = type.replace('.py', '')

                    if name != 'config':
                        instance = self.load_component(profile, name)
                        priority = instance.priority()

                        if priority not in components:
                            components[priority] = [ instance ]
                        else:
                            components[priority].append(instance)
        return components


    def help_search_path(self):
        return self.module_dirs('help')
