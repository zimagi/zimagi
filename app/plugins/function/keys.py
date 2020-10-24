from systems.plugins.index import BaseProvider


class Provider(BaseProvider('function', 'keys')):

    def exec(self, data):
        return list(data.keys())
