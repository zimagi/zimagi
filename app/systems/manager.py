from django.conf import settings

from systems.manage import service, runtime, cluster, template, task
from systems.indexer import Indexer
from utility.terminal import TerminalMixin
from utility.environment import Environment
from utility.runtime import Runtime

import pathlib
import os
import copy
import logging


logger = logging.getLogger(__name__)


class ProviderError(Exception):
    pass


class Manager(
    TerminalMixin,
    service.ManagerServiceMixin,
    runtime.ManagerRuntimeMixin,
    cluster.ManagerClusterMixin,
    task.ManagerTaskMixin,
    template.ManagerTemplateMixin
):
    def __init__(self):
        self.runtime = Runtime()
        self.env = Environment.get_env()

        self.initialize_directories()
        super().__init__()

        self.index = Indexer(self)
        self.index.register_core_module()
        self.index.update_search_path()
        self.index.collect_environment()

        self.active_command = None


    def set_command(self, command):
        self.active_command = command


    def initialize(self):
        self.initialize_directories(True)


    def initialize_directories(self, reinit = False):
        if not reinit:
            self.lib_path = os.path.join(settings.ROOT_LIB_DIR, Environment.get_active_env())
            pathlib.Path(self.lib_path).mkdir(parents = True, exist_ok = True)

        for setting_name, directory in settings.PROJECT_PATH_MAP.items():
            setattr(self, setting_name, os.path.join(self.lib_path, directory))
            pathlib.Path(getattr(self, setting_name)).mkdir(parents = True, exist_ok = True)


    def cleanup(self):
        super().cleanup()


    def get_spec(self, location = None, default = None):
        spec = self.index.spec

        if location is None:
            return spec
        if isinstance(location, str):
            location = location.split('.')

        if default is None:
            default = {}

        for index, element in enumerate(location):
            inner_default = default if index == len(location) - 1 else {}
            spec = spec.get(element, inner_default)

        return copy.deepcopy(spec)


    def get_provider(self, type, name, *args, **options):
        base_provider = self.index.get_plugin_base(type)
        providers = self.index.get_plugin_providers(type, True)

        if name is None or name in ('help', 'base'):
            provider_class = base_provider
        elif name in providers.keys():
            provider_class = providers[name]
        else:
            raise ProviderError("Plugin {} provider {} not supported".format(type, name))

        try:
            return provider_class(type, name, None, *args, **options)
        except Exception as e:
            raise ProviderError("Plugin {} provider {} error: {}".format(type, name, e))
