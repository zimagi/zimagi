from systems.plugins.index import BaseProvider

import datetime


class Provider(BaseProvider('formatter', 'date_time')):

    def format(self, value, record):
        if isinstance(value, float):
            value = int(value)
        try:
            value = datetime.datetime.strptime(str(value), self.field_format)
        except ValueError as e:
            self.error("Value {} is not a valid date time according to pattern: {}".format(value, self.field_format))

        return value
