from systems.plugins.index import BaseProvider

import datetime


class Provider(BaseProvider('validator', 'date_time')):

    def validate(self, value):
        if not isinstance(value, str):
            self.warning("Value {} is not a string".format(value))
            return False

        try:
            datetime.datetime.strptime(value, self.field_format)
        except ValueError as e:
            self.warning("Value {} is not a valid date time according to pattern: {}".format(value, self.field_format))
            return False

        return True
