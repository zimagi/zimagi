from django.conf import settings

from settings.config import Config
from utility.data import ensure_list
from utility.temp import temp_dir
from utility.filesystem import load_file

import os
import sys
import re
import pathlib
import importlib
import shutil
import logging


logger = logging.getLogger(__name__)


class ManagerRuntimeMixin(object):

    def __init__(self):
        self.app_dir = settings.APP_DIR
        self.data_dir = settings.DATA_DIR
        self.module_dir = os.path.join(settings.MODULE_BASE_PATH, self.env.name)
        super().__init__()


    def install_scripts(self, command, display = True):
        for path, config in self.index.get_ordered_modules().items():
            if 'scripts' in config:
                for script_path in ensure_list(config['scripts']):
                    script_path = os.path.join(path, script_path)

                    if os.path.isfile(script_path):
                        with temp_dir() as temp:
                            if display:
                                command.info("Executing script: {}".format(script_path))

                            pathlib.Path(script_path).chmod(0o700)
                            if not command.sh([ script_path ],
                                cwd = temp.base_path,
                                env = { 'MODULE_DIR': path },
                                display = display
                            ):
                                command.error("Installation script failed: {}".format(script_path))

    def parse_requirements(self):
        requirements = []
        for path, config in self.index.get_ordered_modules().items():
            if 'requirements' in config:
                for requirement_path in ensure_list(config['requirements']):
                    requirement_path = os.path.join(path, requirement_path)
                    file_contents = load_file(requirement_path)
                    if file_contents:
                        requirements.extend([ req for req in file_contents.split("\n") if req and req[0].strip() != '#' ])
        return requirements

    def install_requirements(self, command, display = True):
        req_map = {}
        for req in self.parse_requirements():
            # PEP 508
            req_map[re.split(r'[\>\<\!\=\~\s]+', req)[0]] = req

        requirements = list(req_map.values())

        if len(requirements):
            req_text = "\n> ".join(requirements)
            if display:
                command.info("Installing Python requirements:\n> {}".format(req_text))

            if not command.sh(['pip3', 'install'] + requirements, display = display):
                if display:
                    command.error("Installation of requirements failed")
                else:
                    command.error("Installation of requirements failed:\n> {}".format(req_text))
