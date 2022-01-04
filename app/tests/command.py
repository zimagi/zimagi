from .base import BaseTest


class Test(BaseTest):

    def exec(self):
        self.command.info("Running command tests...")

        modules = self.get_modules()
        test_profile = 'test'

        for module in modules:
            module.provider.run_profile(test_profile, ignore_missing = True)
        for module in reversed(modules):
            module.provider.destroy_profile(test_profile, ignore_missing = True)
