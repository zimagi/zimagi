from systems.plugins.index import BaseProvider


class Provider(BaseProvider("function", "keys")):
    def exec(self, data, prefix=None):
        keys = list(data.keys())
        if prefix is None:
            return keys

        for index, key in enumerate(keys):
            keys[index] = f"{prefix}{key}"

        return keys
