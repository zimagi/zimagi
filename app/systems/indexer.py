from collections import OrderedDict
from functools import lru_cache

from django.conf import settings
from django.utils.module_loading import import_string

from systems.index import module, django
from systems.manage.util import ManagerUtilityMixin
from systems.models import index as model_index
from utility.data import Collection, deep_merge

import os
import re
import oyaml
import importlib
import inspect
import threading
import logging


logger = logging.getLogger(__name__)


class Indexer(
    module.IndexerModuleMixin,
    django.IndexerDjangoMixin,
    ManagerUtilityMixin
):
    access_lock = threading.Lock()


    def __init__(self, manager):
        self.manager = manager

        self._spec = {}
        self._roles = {}

        self._base_models = {}
        self._model_mixins = {}
        self._models = {}

        self.module_map = {}

        super().__init__()

    def reload(self):
        self.register_core_module()
        self.update_search_path()
        self.collect_environment()
        self.spec # Trigger build of module map


    def generate(self):
        #self.print_spec()
        self.generate_data_structures()
        print(' ')
        print('=== registered models ===')
        print(self._base_models)
        print(self._model_mixins)
        print(self._models)

        print(' ')
        print('=== class chaining test ===')
        for module_path in (
            'mixins.resource',
            'mixins.provider',
            'config.models',
            'environment.models',
            'group.models',
            'host.models',
            'log.models',
            'module.models',
            'notification.models',
            'schedule.models',
            'state.models',
            'user.models'
        ):
            print("--- data.{} -".format(module_path))
            module = importlib.import_module("data.{}".format(module_path))
            for attribute in dir(module):
                obj = getattr(module, attribute)

                if isinstance(obj, type):
                    print(attribute)
                    print(obj.__bases__)
                    for field in dir(obj):
                        if field[0] != '_':
                            print("> {}".format(field))

        print(' ')
        print('=== django registered models ===')
        from django.apps import apps
        for model in apps.get_models():
            print(model)

        exit()

    def generate_data_structures(self):
        print("== data mixins ====")
        for name, spec in self.spec.get('data_mixins', {}).items():
            print('------------')
            print(name)
            print('------------')
            self._model_mixins[name] = model_index.ModelMixin(name)
            print(self._model_mixins[name].Meta.facade_class)
            print(self._model_mixins[name].Meta.facade_class.__bases__)

        print("== data base ====")
        for name, spec in self.spec.get('data_base', {}).items():
            print('------------')
            print(name)
            print('------------')
            self._base_models[name] = model_index.BaseModel(name)
            print(self._base_models[name].Meta.facade_class)
            print(self._base_models[name].Meta.facade_class.__bases__)

        print("== data models ====")
        for name, spec in self.spec.get('data', {}).items():
            if 'data' in spec:
                print('------------')
                print(name)
                print('------------')
                self._models[name] = model_index.Model(name)
                print(self._models[name].Meta.facade_class)
                print(self._models[name].Meta.facade_class.__bases__)

    @property
    def spec(self):
        if not self._spec:
            def load_directory(base_path):
                if settings.APP_DIR in base_path:
                    module = 'core'
                    module_path = settings.APP_DIR
                else:
                    module = base_path.replace(settings.MODULE_BASE_PATH + '/', '').split('/')[1]
                    module_path = os.path.join(self.manager.module_dir, module)

                module_info = Collection(
                    module = module,
                    path = self._get_module_lib_dir(module_path)
                )

                for name in os.listdir(base_path):
                    file_path = os.path.join(base_path, name)
                    if os.path.isdir(file_path):
                        load_directory(file_path)

                    elif name[0] != '_' and re.match(r'^[^\.]+\.(yml|yaml)$', name, re.IGNORECASE):
                        logger.debug("Loading specification from file: {}".format(file_path))
                        spec_data = self.load_yaml(file_path)

                        for key, info in spec_data.items():
                            self.module_map.setdefault(key, {})
                            if key == 'roles':
                                for name, description in info.items():
                                    self.module_map[key][name] = module_info
                            else:
                                for name, spec in info.items():
                                    self.module_map[key][spec.get('app', name)] = module_info

                        deep_merge(self._spec, spec_data)

            for spec_path in self.get_module_dirs('spec'):
                load_directory(spec_path)

        return self._spec

    def print_spec(self):
        print(oyaml.dump(self.spec, indent=2))


    @property
    def roles(self):
        if not self._roles:
            for name, description in self.spec['roles'].items():
                self._roles[name] = description

            logger.debug("Application roles: {}".format(self._roles))

        return self._roles
