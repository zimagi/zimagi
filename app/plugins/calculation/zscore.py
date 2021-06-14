from statistics import mean, stdev

from systems.plugins.index import BaseProvider


class Provider(BaseProvider('calculation', 'zscore')):

    def calc(self, p):
        values = self.prepare_list(p.a)
        std_dev = stdev(values)
        return (values[-1] - mean(values)) / std_dev if std_dev != 0 else None
