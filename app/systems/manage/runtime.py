import logging
import os
import re

from django.conf import settings
from utility.data import ensure_list
from utility.filesystem import load_file
from utility.temp import temp_dir

logger = logging.getLogger(__name__)


class ManagerRuntimeMixin:
    def __init__(self):
        self.app_name = settings.APP_NAME
        self.app_dir = settings.APP_DIR
        self.data_dir = settings.DATA_DIR
        super().__init__()

    def install_scripts(self, command, display=True):
        if not settings.USER_PASSWORD:
            return

        for path, config in self.index.get_ordered_modules().items():
            if "scripts" in config:
                for script_path in ensure_list(config["scripts"]):
                    script_path = os.path.join(path, script_path)

                    if os.path.isfile(script_path):
                        with temp_dir() as temp:
                            if display:
                                command.info(f"Executing script: {script_path}")

                            if not command.sh(
                                [script_path], cwd=temp.base_path, env={"MODULE_DIR": path}, display=display, sudo=True
                            ):
                                command.error(f"Installation script failed: {script_path}")

    def parse_requirements(self):
        requirements = []
        for path, config in self.index.get_ordered_modules().items():
            if "requirements" in config:
                for requirement_path in ensure_list(config["requirements"]):
                    requirement_path = os.path.join(path, requirement_path)
                    file_contents = load_file(requirement_path)
                    if file_contents:
                        requirements.extend([req for req in file_contents.split("\n") if req and req[0].strip() != "#"])
        return requirements

    def install_requirements(self, command, display=True):
        if not settings.USER_PASSWORD:
            return

        req_map = {}
        for req in self.parse_requirements():
            # PEP 508
            req_map[re.split(r"[\>\<\!\=\~\s]+", req)[0]] = req

        requirements = list(req_map.values())

        if len(requirements):
            req_text = "\n> ".join(requirements)
            if display:
                command.info(f"Installing Python requirements:\n> {req_text}")

            if not command.sh(["pip3", "install"] + requirements, display=display):
                if display:
                    command.error("Installation of requirements failed")
                else:
                    command.error(f"Installation of requirements failed:\n> {req_text}")
