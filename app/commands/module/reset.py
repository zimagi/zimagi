from systems.commands.index import Command


class Reset(Command("module.reset")):
    def exec(self):
        env = self.get_env()
        self.set_state("old_runtime_image", env.runtime_image)

        self.save_env(runtime_image=None)
        self.set_state("module_ensure", True)
        self.success("Successfully reset module runtime")
