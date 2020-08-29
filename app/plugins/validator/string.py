from systems.plugins.index import BaseProvider

import re


class Provider(BaseProvider('validator', 'string')):

    def validate(self, value):
        if not isinstance(value, str):
            self.warning("Value {} is not a string".format(value))
            return False

        if not self.field_empty and len(value) == 0:
            self.warning("Empty strings not allowed")
            return False

        if self.field_pattern:
            pattern = re.compile(self.field_pattern)
            if not pattern.match(value):
                self.warning("Value {} does not match pattern: {}".format(value, self.field_pattern))
                return False

        return True
