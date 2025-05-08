from systems.commands.index import Command


class Version(Command("version")):
    def exec(self):
        self.table([["Server version", self.get_version()]], "version_info")
