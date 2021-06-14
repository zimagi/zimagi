from systems.plugins.index import BaseProvider


class Provider(BaseProvider('calculation', 'divide')):

    def calc(self, p):
        return (p.a / p.b) if self.check(p.a, p.b) else None
