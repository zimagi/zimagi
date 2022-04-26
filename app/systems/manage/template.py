from functools import lru_cache
from shutil import copyfile
from jinja2 import Environment, FileSystemLoader
from django.conf import settings

from utility.data import deep_merge
from utility.filesystem import get_files, create_dir, load_yaml, save_yaml

import os
import importlib
import logging


logger = logging.getLogger(__name__)


class TemplateException(Exception):
    pass


class ManagerTemplateMixin(object):

    def __init__(self):
        self.template_dir = os.path.join(settings.TEMPLATE_BASE_PATH, self.env.name)
        create_dir(self.template_dir)

        self.template_engine = Environment(
            loader = FileSystemLoader(self.template_dir),
            autoescape = False,
            trim_blocks = False,
            block_start_string = '#%',
            block_end_string = '%#',
            variable_start_string = '<{',
            variable_end_string = '}>'
        )
        super().__init__()


    def get_template_path(self, package_name, path = None):
        if path:
            return os.path.join(self.template_dir, package_name, path)
        return os.path.join(self.template_dir, package_name)

    def get_module_path(self, module, path = None):
        module_path = module.provider.module_path(module.name)
        if path:
            return os.path.join(module_path, path)
        return module_path


    @lru_cache(maxsize = None)
    def load_templates(self):
        for path in self.index.get_module_dirs():
            template_path = os.path.join(path, 'templates')
            if os.path.isdir(template_path):
                for name in os.listdir(template_path):
                    template_type_path = os.path.join(template_path, name)
                    if os.path.isdir(template_type_path):
                        if name == 'functions':
                            self.load_template_functions(template_type_path)
                        else:
                            self.load_template_type(template_path, name)


    def load_template_functions(self, function_path):
        for name in os.listdir(function_path):
            function_lib_path = os.path.join(function_path, name)
            if function_lib_path.endswith('.py'):
                spec = importlib.util.spec_from_file_location('module.name', function_lib_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for function in dir(module):
                    self.template_engine.globals[function] = getattr(module, function)


    def load_template_type(self, template_path, type_name):
        template_type_path = os.path.join(template_path, type_name)
        for package_name in os.listdir(template_type_path):
            template_package_path = os.path.join(template_type_path, package_name)
            template_package_home = os.path.join(self.template_dir, type_name, package_name)

            create_dir(template_package_home)

            for file_info in get_files(template_package_path):
                if len(file_info) == 2 and file_info[1] == 'index.yml':
                    package_module_config = load_yaml(os.path.join(*file_info))
                    template_home_index = os.path.join(template_package_home, 'index.yml')
                    package_home_config = load_yaml(template_home_index)

                    if package_home_config is None:
                        package_home_config = package_module_config
                    else:
                        package_home_config = deep_merge(package_home_config, package_module_config)

                    save_yaml(template_home_index, package_home_config)
                else:
                    if file_info[1:-1]:
                        create_dir(os.path.join(*[ template_package_home, *file_info[1:-1] ]))

                    if file_info[1:]:
                        copyfile(
                            os.path.join(*file_info),
                            os.path.join(*[ template_package_home, *file_info[1:] ])
                        )
