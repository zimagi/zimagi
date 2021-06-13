from systems.plugins.index import BaseProvider

import math


class Provider(BaseProvider('calculation', 'level')):

    def calc(self, p):
        if not self.valid_list(p.a):
            return None

        values = self.prepare_list(p.a)
        low = min(values)
        high = max(values)
        range = (high - low)
        return (values[-1] - low) / range if range != 0 else math.nan
