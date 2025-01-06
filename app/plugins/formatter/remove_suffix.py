from systems.plugins.index import BaseProvider


class Provider(BaseProvider("formatter", "remove_suffix")):
    def format(self, value, record):
        value = super().format(value, record)
        if value is not None and self.field_suffix:
            value = value.removesuffix(self.field_suffix)
        return value
