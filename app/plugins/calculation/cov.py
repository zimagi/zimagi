from statistics import mean, stdev

from systems.plugins.index import BaseProvider


class Provider(BaseProvider('calculation', 'cov')):

    def calc(self, p):
        data = self.prepare_list(p.a)
        return stdev(data) / mean(data)
