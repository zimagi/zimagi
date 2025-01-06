from systems.plugins.index import BaseProvider


class Provider(BaseProvider("function", "capitalize")):
    def exec(self, value):
        return value.capitalize()
