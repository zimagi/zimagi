from systems.plugins.index import BaseProvider
from utility.data import number

import math


class Provider(BaseProvider('formatter', 'number')):

    def format(self, value):
        if math.isnan(value):
            return None
        return number(value)
