from collections import OrderedDict
from functools import lru_cache

from django.conf import settings

from utility.filesystem import load_yaml

import os
import logging


logger = logging.getLogger(__name__)


class RequirementError(Exception):
    pass


class IndexerModuleMixin(object):

    def __init__(self):
        self.default_modules = settings.DEFAULT_MODULES
        self.ordered_modules = None
        self.module_index = {}
        super().__init__()


    def help_search_path(self):
        return self.get_module_dirs(os.path.join('help', settings.LANGUAGE_CODE))


    def register_core_module(self):
        self._get_module_config(self.manager.app_dir)

    def collect_environment(self):
        for path, config in self.get_ordered_modules().items():
            if 'env' in config:
                for variable, value in config['env'].items():
                    if variable not in os.environ:
                        os.environ[variable] = str(value)


    def get_ordered_modules(self):
        if not self.ordered_modules:
            self.ordered_modules = OrderedDict()
            self.ordered_modules[self.manager.app_dir] = self._get_module_config(self.manager.app_dir)

            modules = {}
            # for name in os.listdir(self.manager.module_dir):
            #     path = os.path.join(self.manager.module_dir, name)
            #     if os.path.isdir(path):
            #         modules[name] = self._get_module_config(path)

            def process(name, config):
                if 'modules' in config:
                    for parent in config['modules'].keys():
                        if parent in modules:
                            if modules[parent]:
                                process(parent, modules[parent])

                path = os.path.join(self.manager.module_dir, name)
                self.ordered_modules[self._get_module_lib_dir(path)] = config

            for name, config in modules.items():
                if config:
                    process(name, config)

            logger.debug("Loading modules: {}".format(self.ordered_modules))

        return self.ordered_modules

    @lru_cache(maxsize = None)
    def get_module_dirs(self, sub_dir = None, include_core = True):
        module_dirs = []
        for lib_dir in self._get_module_libs(include_core).keys():
            if sub_dir:
                abs_sub_dir = os.path.join(lib_dir, sub_dir)
                if os.path.isdir(abs_sub_dir):
                    module_dirs.append(abs_sub_dir)
            else:
                module_dirs.append(lib_dir)
        return module_dirs

    def get_module_name(self, file):
        if file.startswith(self.manager.app_dir):
            return settings.CORE_MODULE
        return file.replace(self.manager.module_dir + '/', '').split('/')[0]

    def get_module_file(self, *path_components):
        module_file = None

        for module_dir in self.get_module_dirs():
            path = os.path.join(module_dir, *path_components)
            if os.path.isfile(path):
                module_file = path

        if not module_file:
            raise RequirementError("Module file {} not found".format("/".join(path_components)))
        return module_file


    def _get_module_config(self, path):
        if path not in self.module_index:
            mcmi_file = os.path.join(path, 'mcmi.yml')

            if os.path.isfile(mcmi_file):
                self.module_index[path] = load_yaml(mcmi_file)
            else:
                self.module_index[path] = {
                    'lib': '.'
                }
        return self.module_index[path]

    @lru_cache(maxsize = None)
    def _get_module_libs(self, include_core = True):
        module_libs = OrderedDict()
        for path, config in self.get_ordered_modules().items():
            if include_core or path != self.manager.app_dir:
                lib_dir = self._get_module_lib_dir(path)
                if lib_dir:
                    module_libs[lib_dir] = config

        logger.debug("Loading module MCMI libraries: {}".format(module_libs))
        return module_libs

    def _get_module_lib_dir(self, path):
        config = self._get_module_config(path)
        lib_dir = False

        if 'lib' in config:
            lib_dir = config['lib']
            if not lib_dir:
                return False
            elif lib_dir == '.':
                lib_dir = False

        return os.path.join(path, lib_dir) if lib_dir else path
