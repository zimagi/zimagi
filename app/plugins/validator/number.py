from systems.plugins.index import BaseProvider
from utility.data import number

import math


class Provider(BaseProvider('validator', 'number')):

    def validate(self, value):
        try:
            value = number(value)
        except (ValueError, TypeError):
            self.warning("Value {} is not a number".format(value))
            return False

        if not self.field_nan and math.isnan(value):
            self.warning("Value can not be NaN")
            return False

        if self.field_min is not None:
            if value < self.field_min:
                self.warning("Value {} is below minimum allowed: {}".format(value, self.field_min))
                return False

        if self.field_max is not None:
            if value > self.field_max:
                self.warning("Value {} is above maximum allowed: {}".format(value, self.field_max))
                return False

        return True
