import re

from systems.plugins.index import BaseProvider


class Provider(BaseProvider("validator", "string")):
    def validate(self, value, record):
        if not isinstance(value, str):
            self.warning(f"Value {value} is not a string")
            return False

        if not self.field_empty and len(value) == 0:
            self.warning("Empty strings not allowed")
            return False

        if self.field_pattern:
            pattern = re.compile(self.field_pattern)
            if not pattern.match(value):
                self.warning(f"Value {value} does not match pattern: {self.field_pattern}")
                return False

        return True
