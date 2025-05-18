from systems.commands.index import Command


class Install(Command("module.install")):
    def exec(self):
        self.info("Installing module requirements...")
        self.manager.install_scripts(self, self.verbosity == 3)
        self.manager.install_requirements(self, self.verbosity == 3)
        self.success("Successfully installed module requirements")
