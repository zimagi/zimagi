import re

from systems.plugins.index import BaseProvider


class Provider(BaseProvider("formatter", "capitalize")):
    def format(self, value, record):
        value = super().format(value, record)
        if value is not None:
            if self.field_words:
                value = " ".join([item.capitalize() for item in re.split(r"\s+", value)])
            else:
                value = value.capitalize()
        return value
