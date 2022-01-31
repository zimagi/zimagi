from systems.manage import service, runtime, template, task
from systems.indexer import Indexer
from utility.terminal import TerminalMixin
from utility.environment import Environment

import pathlib
import copy
import logging


logger = logging.getLogger(__name__)


class Manager(
    TerminalMixin,
    service.ManagerServiceMixin,
    runtime.ManagerRuntimeMixin,
    task.ManagerTaskMixin,
    template.ManagerTemplateMixin
):
    def __init__(self):
        self.env = Environment.get_env()
        super().__init__()

        pathlib.Path(self.module_dir).mkdir(mode = 0o770, parents = True, exist_ok = True)

        self.index = Indexer(self)
        self.index.register_core_module()
        self.index.update_search_path()
        self.index.collect_environment()


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
