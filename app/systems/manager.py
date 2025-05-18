import copy
import logging
import os
import pathlib

from django.conf import settings
from systems.indexer import Indexer
from systems.manage import cluster, communication, runtime, service, task, template
from utility.data import normalize_value
from utility.runtime import Runtime
from utility.terminal import TerminalMixin
from utility.text import interpolate

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    pass


class Manager(
    TerminalMixin,
    service.ManagerServiceMixin,
    runtime.ManagerRuntimeMixin,
    cluster.ManagerClusterMixin,
    task.ManagerTaskMixin,
    communication.ManagerCommunicationMixin,
    template.ManagerTemplateMixin,
):
    def __init__(self):
        self.runtime = Runtime()

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

    def initialize_directories(self, reinit=False):
        if not reinit:
            self.module_path = self.get_lib_directory("modules")
            self.template_path = self.get_lib_directory("templates")
            self.profiler_path = self.get_lib_directory("profiler")
            self.snapshot_path = self.get_lib_directory("snapshots")
            self.file_path = self.get_lib_directory("files")

        self.backup_ignore = []
        for setting_name, path_info in settings.PROJECT_PATH_MAP.items():
            if isinstance(path_info, dict):
                directory = path_info["directory"]
                if not path_info.get("backup", True):
                    self.backup_ignore.append(directory)
            else:
                directory = path_info

            setattr(self, setting_name, os.path.join(self.file_path, directory))
            pathlib.Path(getattr(self, setting_name)).mkdir(parents=True, exist_ok=True)

    def get_lib_directory(self, type):
        lib_dir = os.path.join(settings.ROOT_LIB_DIR, type)
        pathlib.Path(lib_dir).mkdir(parents=True, exist_ok=True)
        return lib_dir

    def cleanup(self, log_key):
        self.cleanup_task(log_key)
        self.cleanup_communication(log_key)

    def get_spec(self, location=None, default=None):
        spec = self.index.spec

        if location is None:
            return spec
        if isinstance(location, str):
            location = location.split(".")

        if default is None:
            default = {}

        for index, element in enumerate(location):
            inner_default = default if index == len(location) - 1 else {}
            spec = spec.get(element, inner_default)

        return copy.deepcopy(spec)

    def reset_spec(self):
        self.index.reset_spec()

    def interpolate_spec(self, location=None, environment=None):
        if environment is None:
            environment = dict(os.environ)

        return normalize_value(interpolate(self.get_spec(location), environment))

    def get_provider(self, type, name, *args, **options):
        base_provider = self.index.get_plugin_base(type)
        providers = self.index.get_plugin_providers(type, True)

        if name is None or name in ("help", "base"):
            provider_class = base_provider
        elif name in providers.keys():
            provider_class = providers[name]
        else:
            raise ProviderError(f"Plugin {type} provider {name} not supported")

        try:
            return provider_class(type, name, None, *args, **options)
        except Exception as e:
            raise ProviderError(f"Plugin {type} provider {name} error: {e}")
