from systems.plugins.index import BaseProvider


class Provider(BaseProvider("formatter", "title")):
    def format(self, value, record):
        value = super().format(value, record)
        return value.title() if value else None
