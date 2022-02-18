from systems.plugins.index import BaseProvider
from utility.data import number

import math


class Provider(BaseProvider('formatter', 'number')):

    def format(self, value, record):
        try:
            if isinstance(value, str):
                value = float(value)
        except Exception:
            return None

        if value is None or math.isnan(value):
            return None
        return number(value)
