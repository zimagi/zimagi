from systems.plugins.index import BaseProvider
from utility.data import normalize_value


class Provider(BaseProvider("function", "normalize")):
    def exec(self, data):
        return normalize_value(data)
