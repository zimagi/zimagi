from systems.plugins.index import BaseProvider


class Provider(BaseProvider("calculation", "pchange")):
    def calc(self, p):
        return ((p.a - p.b) / p.b) if self.check(p.a, p.b) and p.b != 0 else None
