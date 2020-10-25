from systems.plugins.index import BaseProvider


class Provider(BaseProvider('function', 'value')):

    def exec(self, data, keys, default = None):
        if isinstance(keys, str):
            keys = key.split('.')

        last_index = len(keys) - 1
        for index, key in enumerate(keys):
            if index == last_index:
                data = data.get(key, default)
            else:
                data = data.get(key, {})

        return data
