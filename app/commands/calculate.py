from systems.commands.index import Command
from systems.commands.calculator import Calculator


class Calculate(Command('calculate')):

    def exec(self):
        Calculator(self, display_only = self.show_spec, reset = self.reset).run(
            required_names = self.calculation_names,
            required_tags = self.tags,
            ignore_requirements = self.ignore_requirements,
            field_values = self.field_values
        )
