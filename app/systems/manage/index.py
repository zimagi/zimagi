from collections import OrderedDict
from functools import lru_cache

from django.utils.module_loading import import_string

import os
import logging


logger = logging.getLogger(__name__)


class ManagerIndexMixin(object):

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
