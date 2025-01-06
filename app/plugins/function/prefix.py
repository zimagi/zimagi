from systems.plugins.index import BaseProvider
from utility.data import ensure_list


class Provider(BaseProvider("function", "prefix")):
    def exec(self, values, prefix=None, keys=None):
        if isinstance(values, dict):
            values = list(values.keys())
        else:
            values = ensure_list(values)

        if prefix is None:
            return values

        for index, value in enumerate(values):
            if keys and isinstance(value, (list, tuple, dict)):
                for key in keys.split("."):
                    if isinstance(value, (list, tuple)):
                        value = value[int(key)]
                    else:
                        value = value[key]

            values[index] = f"{prefix}{value}"
        return values
