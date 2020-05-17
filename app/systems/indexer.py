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
        self.print_spec()
        self.generate_data_structures()
        self.print_results()

    def generate_data_structures(self):
        logger.debug("* Generating data mixins")
        for name, spec in self.spec.get('data_mixins', {}).items():
            logger.debug(" > {}".format(name))
            self._model_mixins[name] = model_index.ModelMixin(name)
            logger.debug("    - {}".format(self._model_mixins[name]))
            logger.debug("    - {}".format(self._model_mixins[name]._meta.facade_class))

        logger.debug("* Generating base data models")
        for name, spec in self.spec.get('data_base', {}).items():
            logger.debug(" > {}".format(name))
            self._base_models[name] = model_index.BaseModel(name)
            logger.debug("    - {}".format(self._base_models[name]))
            logger.debug("    - {}".format(self._base_models[name]._meta.facade_class))

        logger.debug("* Generating data models")
        for name, spec in self.spec.get('data', {}).items():
            if 'data' in spec:
                logger.debug(" > {}".format(name))
                self._models[name] = model_index.Model(name)
                logger.debug("    - {}".format(self._models[name]))
                logger.debug("    - {}".format(self._models[name]._meta.facade_class))


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


    @property
    def roles(self):
        if not self._roles:
            for name, description in self.spec['roles'].items():
                self._roles[name] = description

            logger.debug("Application roles: {}".format(self._roles))

        return self._roles


    def print_spec(self):
        logger.debug(oyaml.dump(self.spec, indent = 2))

    def print_results(self):
        logger.debug('* Registered models')
        logger.debug(self._base_models)
        logger.debug(self._model_mixins)
        logger.debug(self._models)

        #print(model_index.Model('environment').facade.get_env())

        logger.debug('* Python module registry')
        for module_path in (
            'base.resource',
            'base.environment',
            'mixins.environment',
            'mixins.group',
            'mixins.config',
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
            logger.debug(" --- data.{}".format(module_path))
            module = importlib.import_module("data.{}".format(module_path))
            for attribute in dir(module):
                obj = getattr(module, attribute)

                if isinstance(obj, type):
                    logger.debug("  - {} <{}>".format(attribute, obj.__bases__))
                    # for field in dir(obj):
                    #     if field[0] != '_':
                    #         print("> {}".format(field))

        logger.debug('* Django registered models')
        from django.apps import apps
        for model in apps.get_models():
            logger.debug(" - {}".format(model))

        exit()
