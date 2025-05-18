import random

from systems.plugins.index import BaseProvider


class Provider(BaseProvider("function", "random_keys")):
    def exec(self, dict_value, limit=None):
        keys = list(dict_value.keys())
        random.shuffle(keys)

        if limit:
            return keys[: min(int(limit), len(keys))]
        return keys
