from systems.manage import service, init, index, util

import pathlib
import logging


logger = logging.getLogger(__name__)


class Manager(
    service.ManagerServiceMixin,
    init.ManagerInitializationMixin,
    index.ManagerIndexMixin,
    util.ManagerUtilityMixin
):
    def __init__(self):
        super().__init__()
        self.reload()

    def reload(self):
        pathlib.Path(self.module_dir).mkdir(mode = 0o700, parents = True, exist_ok = True)

        self.module_config(self.app_dir)
        self.update_search_path()
        self.collect_environment()
        self.load_plugins()
