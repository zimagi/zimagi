from systems.plugins.index import BaseProvider


class Provider(BaseProvider("function", "lstrip")):
    def exec(self, value, prefix=None):
        value = value.strip()
        if prefix and value.startswith(prefix):
            value = value[len(prefix) :]
        return value
