from systems.commands.index import Command
from systems.commands.importer import Importer


class Import(Command('import')):

    def exec(self):
        Importer(self, display_only = self.show_spec).run(
            required_names = self.import_names,
            required_tags = self.tags,
            ignore_requirements = self.ignore_requirements,
            field_values = self.field_values
        )
