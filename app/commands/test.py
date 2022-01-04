from systems.commands.index import Command
from utility.filesystem import get_files

import importlib


class Test(Command('test')):

    def exec(self):
        supported_types = self._get_test_types()

        def run_tests(type):
            if type not in supported_types:
                self.error("Test type {} is not in supported types: {}".format(type, supported_types))

            module = importlib.import_module("tests.{}".format(type))
            module.Test(self, self, self.host_name).exec()

        self.run_list(
            supported_types if not self.test_types else self.test_types,
            run_tests
        )

    def _get_test_types(self):
        test_types = []
        for test_path in self.manager.index.get_module_files('tests'):
            for file_components in get_files(test_path):
                file = file_components[-1]
                if file.endswith('.py') and file != 'base.py':
                    test_types.append(file_components[-1].removesuffix('.py'))
        return test_types
