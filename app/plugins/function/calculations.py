import re

from systems.plugins.index import BaseProvider


class Provider(BaseProvider("function", "calculations")):
    def exec(self, pattern):
        calculation_names = []
        for name in self.manager.get_spec("calculation").keys():
            if re.match(rf"{pattern}", name):
                calculation_names.append(name)
        return calculation_names
