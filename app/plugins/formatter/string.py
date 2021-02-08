from systems.plugins.index import BaseProvider

import math


class Provider(BaseProvider('formatter', 'string')):

    def format(self, value, record):
        if not value or (not isinstance(value, str) and math.isnan(value)):
            return None
        return str(value)
