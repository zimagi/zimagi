import datetime

from systems.plugins.index import BaseProvider


class Provider(BaseProvider("formatter", "date_time")):
    def format(self, value, record):
        if isinstance(value, float):
            value = int(value)
        try:
            value = datetime.datetime.strptime(str(value), self.field_format)
        except ValueError as e:
            self.error(f"Value {value} is not a valid date time according to pattern: {self.field_format}")

        return value
