from systems.plugins.index import BaseProvider


class Provider(BaseProvider('function', 'values')):

    def exec(self, data):
        return list(data.values())
