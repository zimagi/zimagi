from systems.plugins.index import BaseProvider


class Provider(BaseProvider('formatter', 'lower')):

    def format(self, value, record):
        value = super().format(value, record)
        return value.lower() if value else None
