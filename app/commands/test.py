from systems.commands.index import Command
from utility.filesystem import get_files

import importlib


class Test(Command('test')):

    def exec(self):
        for type in ('command', 'api'):
            if not self.test_type or type in self.test_types:
                getattr(self, "run_{}_tests".format(type))()


    def run_command_tests(self):
        self.info("Running command tests...")
        for module in self.get_instances(self._module):
            module.provider.run_profile('test', ignore_missing = True)

    def run_api_tests(self):
        host = self.get_instance(self._host, self.host_name, required = False)

        def run_tests(module_name):
            module = importlib.import_module(module_name)
            module.Test(self, host).exec()

        if host:
            self.info("Running API tests...")
            self.run_list(self._get_test_files('api'), run_tests)


    def _get_test_files(self, type = 'api'):
        test_files = []
        for test_path in self.manager.index.get_module_files('tests', type):
            for file_components in get_files(test_path):
                file = file_components[-1]
                if file.endswith('.py') and file != 'base.py':
                    test_files.append("tests.{}.".format(type) + ".".join(file_components[1:]).removesuffix('.py'))
        return test_files
