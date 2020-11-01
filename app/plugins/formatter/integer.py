from systems.plugins.index import BaseProvider


class Provider(BaseProvider('formatter', 'integer')):

    def format(self, value, record):
        value = super().format(value, record)
        return value if value is None else int(value)
