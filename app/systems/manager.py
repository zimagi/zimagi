from systems.manage import service, runtime, template
from systems.indexer import Indexer
from utility.environment import Environment

import pathlib
import logging


logger = logging.getLogger(__name__)


class Manager(
    service.ManagerServiceMixin,
    runtime.ManagerRuntimeMixin,
    template.ManagerTemplateMixin
):
    def __init__(self):
        self.env = Environment.get_env()

        super().__init__()

        pathlib.Path(self.module_dir).mkdir(mode = 0o700, parents = True, exist_ok = True)

        self.index = Indexer(self)
        self.index.register_core_module()
        self.index.update_search_path()
        self.index.collect_environment()

        self.load_templates()


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

        return spec