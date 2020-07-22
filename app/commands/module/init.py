from systems.commands.index import Command


class Init(Command('module.init')):

    def exec(self):
        def init_modules():
            if self.full:
                self._module._ensure(self, True)
            else:
                for module in self.get_instances(self._module):
                    module.provider.update()

                self.exec_local('module install', {
                    'verbosity': self.verbosity
                })

        self.run_exclusive('module_init', init_modules, timeout = self.timeout)
