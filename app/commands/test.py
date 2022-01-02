from systems.commands.index import Command


class Test(Command('test')):

    def exec(self):
        def run_profile(module):
            module.provider.run_profile('test', ignore_missing = True)

        self.info("Running module tests...")
        self.run_list(self.get_instances(self._module), run_profile)
