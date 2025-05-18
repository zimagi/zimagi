from systems.plugins.index import BaseProvider
from utility.data import ensure_list


class Provider(BaseProvider("function", "join")):
    def exec(self, *elements):
        values = []

        for element in elements:
            values.extend(ensure_list(element))

        return values
