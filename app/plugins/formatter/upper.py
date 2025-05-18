from systems.plugins.index import BaseProvider


class Provider(BaseProvider("formatter", "upper")):
    def format(self, value, record):
        value = super().format(value, record)
        return value.upper() if value else None
