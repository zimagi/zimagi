from systems.plugins.index import BaseProvider


class Provider(BaseProvider("function", "substitute")):
    def exec(self, value, search, replacement):
        return value.replace(search, replacement)
