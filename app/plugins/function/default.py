from systems.plugins.index import BaseProvider
from utility.data import normalize_value


class Provider(BaseProvider("function", "default")):
    def exec(self, data, default):
        value = normalize_value(data)
        return default if value is None else value
