from systems.plugins.index import BaseProvider


class Provider(BaseProvider('calculation', 'min_max_scale')):

    def calc(self, p):
        values = self.prepare_list(p.a)
        low = min(values)
        range = (max(values) - low)
        return (values[-1] - low) / range if range != 0 else None
