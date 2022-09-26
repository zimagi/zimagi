from collections import OrderedDict
from functools import lru_cache

from django.conf import settings

from utility.data import ensure_list, deep_merge
from utility.filesystem import load_yaml, save_yaml

import os
import logging


logger = logging.getLogger(__name__)


class RequirementError(Exception):
    pass


class IndexerModuleMixin(object):

    def __init__(self):
        self.default_modules = ensure_list(settings.DEFAULT_MODULES)
        self.remote_module_names = {}
        self.ordered_modules = None
        self.module_index = {}
        self.module_dependencies = {}
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
            for name in os.listdir(self.manager.module_dir):
                path = os.path.join(self.manager.module_dir, name)
                if os.path.isdir(path):
                    modules[name] = self._get_module_config(path)
                    if 'remote' in modules[name]:
                        self.remote_module_names[modules[name]['remote']] = name

            def process(name, config):
                if 'modules' in config:
                    for parent in ensure_list(config['modules']):
                        if parent and 'remote' in parent:
                            parent_name = self.remote_module_names.get(parent['remote'], None)
                            if parent_name and parent_name in modules:
                                if modules[parent_name]:
                                    self.module_dependencies.setdefault(parent_name, [])
                                    if name not in self.module_dependencies[parent_name]:
                                        self.module_dependencies[parent_name].append(name)

                                    process(parent_name, modules[parent_name])

                path = os.path.join(self.manager.module_dir, name)
                self.ordered_modules[self._get_module_lib_dir(path)] = config

            for name, config in modules.items():
                process(name, config)

            logger.debug("Loading modules: {}".format(self.ordered_modules))

        return self.ordered_modules

    def get_default_module_names(self):
        remote_names = []
        for module in self.default_modules:
            remote_names.append(self.remote_module_names[module['remote']])
        return remote_names

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
            if os.path.exists(path):
                module_file = path

        if not module_file:
            raise RequirementError("Module file {} not found".format("/".join(path_components)))
        return module_file

    def get_module_files(self, *path_components):
        module_files = []

        for module_dir in self.get_module_dirs():
            path = os.path.join(module_dir, *path_components)
            if os.path.exists(path):
                module_files.append(path)

        return module_files


    def save_module_config(self, module_name, config):
        module_path = os.path.join(self.manager.module_dir, module_name)
        zimagi_config_path = os.path.join(module_path, '.zimagi.yml')
        loaded_config = {}

        if os.path.isfile(zimagi_config_path):
            loaded_config = load_yaml(zimagi_config_path)
            if not isinstance(loaded_config, dict):
                loaded_config = {}

        config = deep_merge(loaded_config, config)
        save_yaml(zimagi_config_path, config)

    def _get_module_config(self, path):
        if path not in self.module_index:
            self.module_index[path] = {}

            for config_file in ('zimagi.yml', '.zimagi.yml'):
                zimagi_config = os.path.join(path, config_file)
                if os.path.isfile(zimagi_config):
                    self.module_index[path] = deep_merge(self.module_index[path], load_yaml(zimagi_config))

            if not self.module_index.get(path, None):
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

        logger.debug("Loading module Zimagi libraries: {}".format(module_libs))
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
