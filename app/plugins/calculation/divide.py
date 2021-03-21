from systems.plugins.index import BaseProvider

import math


class Provider(BaseProvider('calculation', 'divide')):

    def calc(self, p):
        if self.check(p.a, p.b):
            return (p.a / p.b) if p.b != 0 else math.nan
        return None
