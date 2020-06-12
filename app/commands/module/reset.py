from systems.commands.index import Command


class Reset(Command('module.reset')):

    def exec(self):
        env = self.get_env()
        env.runtime_image = None
        env.save()
        self.set_state('module_ensure', True)
        self.success("Successfully reset module runtime")
