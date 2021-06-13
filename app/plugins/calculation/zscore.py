from systems.plugins.index import BaseProvider

import math
import statistics


class Provider(BaseProvider('calculation', 'zscore')):

    def calc(self, p):
        if not self.valid_list(p.a):
            return None

        values = self.prepare_list(p.a)
        mean = statistics.mean(values)
        stdev = statistics.stdev(values)
        return (values[-1] - mean) / stdev if stdev != 0 else math.nan
