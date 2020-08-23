from systems.plugins.index import BaseProvider


class Provider(BaseProvider('formatter', 'joiner')):

    def format(self, value):
        if isinstance(value, (list, tuple)):
            value = self.field_join.join(value)
        return value
