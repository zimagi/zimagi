from utility.filesystem import get_files

import importlib


class BaseTest(object):

    def __init__(self, command, host_name):
        self.command = command
        self.manager = command.manager
        self.host_name = host_name


    def exec(self):
        raise NotImplementedError("Subclasses of BaseTest must implement exec method")


    def get_host(self):
        return self.command.get_instance(self.command._host, self.host_name, required = False)

    def get_modules(self):
        modules = { module.name: module for module in self.command.get_instances(self.command._module) }
        ordered_modules = []

        for name in [ self.manager.index.get_module_name(path) for path in self.manager.index.get_ordered_modules().keys() ]:
            if name in modules:
                ordered_modules.append(modules[name])
        return ordered_modules


    def get_test_libs(self, type):
        test_libs = []
        for test_path in self.manager.index.get_module_files('tests', type):
            for file_components in get_files(test_path):
                file = file_components[-1]
                if file.endswith('.py') and file != 'base.py':
                    test_libs.append("tests.{}.".format(type) + ".".join(file_components[1:]).removesuffix('.py'))
        return test_libs

    def run_tests(self, module_name, *args, **kwargs):
        module = importlib.import_module(module_name)
        module.Test(*[ self.command, *args ], **kwargs).exec()
