from systems.manage import service, runtime
from systems.indexer import Indexer

import pathlib
import logging


logger = logging.getLogger(__name__)


class Manager(
    service.ManagerServiceMixin,
    runtime.ManagerRuntimeMixin
):
    def __init__(self):
        super().__init__()
        self.index = Indexer(self)
        self.reload()

    def reload(self):
        pathlib.Path(self.module_dir).mkdir(mode = 0o700, parents = True, exist_ok = True)
        self.index.reload()
