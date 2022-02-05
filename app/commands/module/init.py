from systems.commands.index import Command


class Init(Command('module.init')):

    def bootstrap_ensure(self):
        return False

    def exec(self):
        def init_modules():
            initialized = self.get_state('startup_initialized')
            if self.reset or not initialized:
                self.ensure_resources(reinit = True)
            self.set_state('startup_initialized', True)

        self.run_exclusive('module_init', init_modules, timeout = self.timeout)
