from systems.plugins.index import BaseProvider
from utility.data import ensure_list


class Provider(BaseProvider('function', 'prefix')):

    def exec(self, values, prefix = None):
        values = ensure_list(values)

        if prefix is None:
            return values

        for index, value in enumerate(values):
            values[index] = "{}{}".format(prefix, value)

        return values
