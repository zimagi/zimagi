from functools import lru_cache

from django.apps import apps

import os
import sys
import importlib
import shutil
import logging


logger = logging.getLogger(__name__)


class IndexerDjangoMixin(object):

    def __init__(self):
        super().__init__()


    def update_search_path(self):
        for lib_dir in self.get_module_dirs(None, False):
            sys.path.append(lib_dir)
        importlib.invalidate_caches()


    @lru_cache(maxsize = None)
    def get_settings_modules(self):
        modules = []
        for module_dir in self.get_module_dirs(None, False):
            interface_dir = os.path.join(module_dir, 'interface')

            if os.path.isdir(interface_dir):
                for name in os.listdir(interface_dir):
                    settings_file = os.path.join(interface_dir, name, 'settings.py')

                    if name[0] != '_' and os.path.isfile(settings_file):
                        try:
                            module = "interface.{}.settings".format(name)
                            modules.append(importlib.import_module(module))
                        except Exception as e:
                            shutil.rmtree(module_dir, ignore_errors = True)
                            raise e
        return modules


    @lru_cache(maxsize = None)
    def get_installed_apps(self):
        apps = []
        for module_dir in self.get_module_dirs():
            data_dir = os.path.join(module_dir, 'data')

            if os.path.isdir(data_dir):
                for name in os.listdir(data_dir):
                    if name[0] != '_' and os.path.isdir(os.path.join(data_dir, name)) and name not in ('base', 'mixins'):
                        apps.append("data.{}".format(name))

        logger.debug("Installed Django applications: {}".format(apps))
        return apps

    @lru_cache(maxsize = None)
    def get_installed_middleware(self):
        middleware = []
        for middleware_dir in self.get_module_dirs('middleware'):
            for name in os.listdir(middleware_dir):
                if name[0] != '_':
                    middleware.append("middleware.{}.Middleware".format(name))

        logger.debug("Installed Django middleware: {}".format(middleware))
        return middleware


    @lru_cache(maxsize = None)
    def get_models(self):
        models = []
        for model in apps.get_models():
            if getattr(model, 'facade', None):
                models.append(model)
        return models
