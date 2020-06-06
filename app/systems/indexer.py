from collections import OrderedDict
from functools import lru_cache

from django.conf import settings
from django.apps import apps

from systems.index import module, django, plugin, component
from systems.models import index as model_index
from systems.command import index as command_index
from systems.plugins import index as plugin_index
from utility.data import Collection, deep_merge
from utility.filesystem import load_yaml

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
    plugin.IndexerPluginMixin,
    component.IndexerComponentMixin
):
    def __init__(self, manager):
        self.manager = manager

        self._spec = OrderedDict()
        self._roles = {}

        self._base_models = {}
        self._model_mixins = {}
        self._models = {}

        self.module_map = {}
        self.model_class_path = {}
        self.model_class_facades = {}

        self._base_commands = {}
        self._command_mixins = {}
        self._command_tree = {}

        self._base_plugins = {}

        super().__init__()

    def reload(self):
        self.register_core_module()
        self.update_search_path()
        self.collect_environment()
        self.spec # Trigger build of module map


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
                        spec_data = load_yaml(file_path)

                        for key, info in spec_data.items():
                            self.module_map.setdefault(key, {})
                            if key == 'roles':
                                for name, description in info.items():
                                    self.module_map[key][name] = module_info
                            else:
                                for name, spec in info.items():
                                    app_name = spec.get('app', name)
                                    self.module_map[key][app_name] = module_info

                                    if key in ('data', 'data_base', 'data_mixins'):
                                        module_name = model_index.get_module_name(key, app_name)
                                        model_class = model_index.get_model_name(name, spec)
                                        dynamic_class = model_index.get_dynamic_class_name(model_class)

                                        self.model_class_path[model_class] = module_name
                                        self.model_class_path[dynamic_class] = module_name

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


    @lru_cache(maxsize = None)
    def get_facade_index(self):
        facade_index = {}
        for model in self.get_models():
            facade = model.facade
            facade_index[facade.name] = facade
        return facade_index


    @property
    def command_tree(self):
        return self._command_tree

    def find_command(self, *args, **kwargs):
        return command_index.find_command(*args, **kwargs)


    def generate(self):
        self.print_spec()
        self.generate_data_structures()
        self.generate_commands()
        self.generate_plugins()
        self.print_results()


    def generate_data_structures(self):
        logger.info("* Generating data mixins")
        for name, spec in self.spec.get('data_mixins', {}).items():
            logger.info(" > {}".format(name))
            self._model_mixins[name] = model_index.ModelMixin(name)
            logger.info("    - {}".format(self._model_mixins[name]))
            logger.info("    - {}".format(self._model_mixins[name].facade_class))

        logger.info("* Generating base data models")
        for name, spec in self.spec.get('data_base', {}).items():
            logger.info(" > {}".format(name))
            self._base_models[name] = model_index.BaseModel(name)
            logger.info("    - {}".format(self._base_models[name]))
            logger.info("    - {}".format(self._base_models[name].facade_class))

        logger.info("* Generating data models")
        for name, spec in self.spec.get('data', {}).items():
            logger.info(" > {}".format(name))
            self._models[name] = model_index.Model(name, True)
            logger.info("    - {}".format(self._models[name]))
            logger.info("    - {}".format(self._models[name].facade_class))


    def generate_commands(self):
        logger.info("* Generating command mixins")
        for name, spec in self.spec.get('command_mixins', {}).items():
            logger.info(" > {}".format(name))
            self._command_mixins[name] = command_index.CommandMixin(name)
            logger.info("    - {}".format(self._command_mixins[name]))

        logger.info("* Generating base commands")
        for name, spec in self.spec.get('command_base', {}).items():
            logger.info(" > {}".format(name))
            self._base_commands[name] = command_index.BaseCommand(name)
            logger.info("    - {}".format(self._base_commands[name]))

        logger.info("* Generating command tree")
        self._command_tree = command_index.generate_command_tree(
            self.spec.get('command', {})
        )


    def generate_plugins(self):
        logger.info("* Generating base plugins")
        for name, spec in self.spec.get('plugin', {}).items():
            logger.info(" > {}".format(name))
            self._base_plugins[name] = plugin_index.BasePlugin(name, True)
            logger.info("    - {}".format(self._base_plugins[name]))
            self.load_plugin_providers(name, spec, self._base_plugins[name])


    def print_spec(self):
        logger.debug(oyaml.dump(self.spec, indent = 2))

    def print_command_tree(self, command, prefix = ''):
        logger.info("{} {}".format(prefix, command))
        if getattr(command, 'get_subcommands', None):
            for subcommand in command.get_subcommands():
                self.print_command_tree(subcommand, "{} > ".format(prefix))

    def print_plugins(self):
        for name, klass in self._base_plugins.items():
            logger.info("{}: {}".format(name, klass))

    def print_results(self):
        logger.info('* Registered models')
        logger.info(self._base_models)
        logger.info(self._model_mixins)
        logger.info(self._models)

        logger.info('* Django registered models')
        for model in apps.get_models():
            logger.info(" - {}".format(model))
            model_index.display_model_info(model)

        logger.info('* Command tree')
        self.print_command_tree(self._command_tree)

        logger.info('* Plugins')
        self.print_plugins()
