from statistics import stdev

from systems.plugins.index import BaseProvider


class Provider(BaseProvider("calculation", "stdev")):
    def calc(self, p):
        return stdev(self.prepare_list(p.a))
