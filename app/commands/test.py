from systems.commands.index import Command
from utility.filesystem import get_files

import importlib


class Test(Command('test')):

    def exec(self):
        self.disable_logging()

        supported_types = self._get_test_types()

        for type in supported_types if not self.test_types else self.test_types:
            if type not in supported_types:
                self.error("Test type {} is not in supported types: {}".format(type, ", ".join(supported_types)))

            self.info("Running {} tests...".format(type))
            module = importlib.import_module("tests.{}".format(type))
            module.Test(self).exec()


    def _get_test_types(self):
        test_types = []
        for test_path in self.manager.index.get_module_files('tests'):
            for file_components in get_files(test_path):
                file = file_components[-1]
                if len(file_components) == 2 and file.endswith('.py') and file != 'base.py':
                    test_types.append(file.removesuffix('.py'))
        return test_types
