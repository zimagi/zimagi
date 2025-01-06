import math

from systems.plugins.index import BaseProvider
from utility.data import number


class Provider(BaseProvider("validator", "number")):
    def validate(self, value, record):
        try:
            value = number(value)
        except (ValueError, TypeError):
            self.warning(f"Value {value} is not a number")
            return False

        if not self.field_nan and math.isnan(value):
            self.warning("Value can not be NaN")
            return False

        if self.field_min is not None:
            if value < self.field_min:
                self.warning(f"Value {value} is below minimum allowed: {self.field_min}")
                return False

        if self.field_max is not None:
            if value > self.field_max:
                self.warning(f"Value {value} is above maximum allowed: {self.field_max}")
                return False

        return True
