from systems.commands.index import Command


class Test(Command('test')):

    def exec(self):
        self.info("Running module tests...")
        for module in self.get_instances(self._module):
            module.provider.run_profile('test', ignore_missing = True)
