from systems.plugins.index import BaseProvider


class Provider(BaseProvider('calculation', 'division')):

    def calc(self, p):
        return (p.a / p.b) if self.check(p.a, p.b) and p.b != 0 else None
