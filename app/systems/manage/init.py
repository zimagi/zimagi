from settings import core as settings

from settings.config import Config
from utility.data import ensure_list
from utility.temp import temp_dir

import os
import sys
import re
import pathlib
import importlib
import shutil
import logging


logger = logging.getLogger(__name__)


class ManagerInitializationMixin(object):

    def __init__(self):
        super().__init__()
        self.app_dir = settings.APP_DIR
        self.data_dir = settings.DATA_DIR
        self.config = Config.load(settings.RUNTIME_PATH, {})
        self.env = self.config.get('MCMI_ENV', settings.DEFAULT_ENV_NAME)
        self.module_dir = os.path.join(settings.MODULE_BASE_PATH, self.env)


    def update_search_path(self):
        for lib_dir in self.get_module_libs().keys():
            sys.path.append(lib_dir)
        importlib.invalidate_caches()

    def collect_environment(self):
        for path, config in self.get_modules().items():
            if 'env' in config:
                for variable, value in config['env'].items():
                    os.environ[variable] = str(value)


    def settings_modules(self):
        modules = []
        for module_dir in self.module_dirs(None, False):
            interface_dir = os.path.join(module_dir, 'interface')

            if os.path.isdir(interface_dir):
                for name in os.listdir(interface_dir):
                    settings_file = os.path.join(interface_dir, name, 'settings.py')

                    if name[0] != '_' and os.path.isfile(settings_file):
                        try:
                            module = "interface.{}.settings".format(name)
                            modules.append(importlib.import_module(module))
                        except Exception as e:
                            shutil.rmtree(module_dir, ignore_errors = True)
                            raise e
        return modules

    def installed_apps(self):
        apps = []
        for module_dir in self.module_dirs():
            data_dir = os.path.join(module_dir, 'data')
            interface_dir = os.path.join(module_dir, 'interface')

            if os.path.isdir(interface_dir):
                for name in os.listdir(interface_dir):
                    if name[0] != '_':
                        apps.append("interface.{}".format(name))

            if os.path.isdir(data_dir):
                for name in os.listdir(data_dir):
                    if name[0] != '_':
                        apps.append("data.{}".format(name))

        logger.debug("Installed Django applications: {}".format(apps))
        return apps

    def installed_middleware(self):
        middleware = []
        for middleware_dir in self.module_dirs('middleware'):
            for name in os.listdir(middleware_dir):
                if name[0] != '_':
                    middleware.append("middleware.{}.Middleware".format(name))

        logger.debug("Installed Django middleware: {}".format(middleware))
        return middleware


    def install_scripts(self, command, display = True):
        for path, config in self.get_modules().items():
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
        for path, config in self.get_modules().items():
            if 'requirements' in config:
                for requirement_path in ensure_list(config['requirements']):
                    requirement_path = os.path.join(path, requirement_path)
                    file_contents = self.load_file(requirement_path)
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


    def load_env(self, env_name, variables = None):
        if not variables:
            variables = {}

        env_file = os.path.join(self.data_dir, "{}.env".format(env_name))
        return Config.load(env_file, {})
