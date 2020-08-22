from systems.commands.index import Command
from systems.commands.importer import Importer


class Import(Command('import')):

    def exec(self):
        Importer(self).run(
            required_names = self.import_names,
            ignore_requirements = self.ignore_requirements
        )
