from systems.plugins.index import BaseProvider


class Substitute(BaseProvider('function', 'substitute')):

    def exec(self, value, search, replace):
        return value.replace(search, replace)
