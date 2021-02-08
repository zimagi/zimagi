from systems.plugins.index import BaseProvider


class Provider(BaseProvider('formatter', 'capitalize')):

    def format(self, value, record):
        value = super().format(value, record)
        return value[0].capitalize() + value[1:] if value else None
