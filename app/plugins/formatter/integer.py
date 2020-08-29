from systems.plugins.index import BaseProvider


class Provider(BaseProvider('formatter', 'integer')):

    def format(self, value):
        value = super().format(value)
        return value if value is None else int(value)
