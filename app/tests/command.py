from django.conf import settings
from .base import BaseTest


class Test(BaseTest):

    def exec(self):
        modules = self.get_modules()
        test_profile = 'test'

        self.run_profiles(modules, test_profile)
        self.destroy_profiles(modules, test_profile)


    def get_modules(self):
        modules = { module.name: module for module in self.command.get_instances(self.command._module) }
        ordered_modules = []

        for name in [ self.manager.index.get_module_name(path) for path in self.manager.index.get_ordered_modules().keys() ]:
            if name in modules:
                ordered_modules.append(modules[name])
        return ordered_modules


    def run_profiles(self, modules, test_profile):
        for module in modules:
            self.command.notice("Running {} operations...".format(module))
            self.command.mute = not settings.DEBUG_COMMAND_PROFILES
            module.provider.run_profile(test_profile, ignore_missing = True)
            self.command.mute = False

    def destroy_profiles(self, modules, test_profile):
        for module in reversed(modules):
            self.command.notice("Destroying {} resources...".format(module))
            self.command.mute = not settings.DEBUG_COMMAND_PROFILES
            module.provider.destroy_profile(test_profile, ignore_missing = True)
            self.command.mute = False
