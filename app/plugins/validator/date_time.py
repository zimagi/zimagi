import datetime

from systems.plugins.index import BaseProvider
from utility.data import ensure_list


class Provider(BaseProvider("validator", "date_time")):
    def validate(self, value, record):
        if not self.field_empty and not value:
            self.warning("Empty strings not allowed")
            return False

        if value:
            if isinstance(value, float):
                value = int(value)

            for date_format in ensure_list(self.field_format):
                try:
                    datetime.datetime.strptime(str(value), date_format)
                    return True
                except ValueError as e:
                    pass

            self.warning(f"Value {value} is not a valid date time according to pattern: {self.field_format}")
            return False
        return True
