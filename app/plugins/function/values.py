from systems.plugins.index import BaseProvider


class Provider(BaseProvider('function', 'values')):

    def exec(self, data, keys = None):
        if keys is None:
            return list(data.values())

        def get_value(inner_data, inner_keys):
            last_index = len(inner_keys) - 1
            for index, inner_key in enumerate(inner_keys):
                if index == last_index:
                    inner_data = inner_data.get(inner_key, None)
                else:
                    inner_data = inner_data.get(inner_key, {})
            return inner_data

        keys = keys.split('.')
        values = []
        if isinstance(data, (list, tuple)):
            for index, value in enumerate(data):
                values.append(get_value(value, keys))
        else:
            for key, value in data.items():
                values.append(get_value(value, keys))

        return values
