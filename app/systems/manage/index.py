from collections import OrderedDict
from functools import lru_cache

from django.utils.module_loading import import_string

import os
import logging


logger = logging.getLogger(__name__)


class ManagerIndexMixin(object):

    def load_plugins(self):
        self.plugins = {}
        for plugin_dir in self.get_module_dirs('plugins'):
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
        for component_dir in self.get_module_dirs('components'):
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
