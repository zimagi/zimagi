from statistics import mean, stdev

from systems.plugins.index import BaseProvider


class Provider(BaseProvider('calculation', 'zscore')):

    def calc(self, p):
        values = self.prepare_list(p.a)
        return (values[-1] - mean(values)) / stdev(values)
