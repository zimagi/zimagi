from systems.plugins.index import BaseProvider


class Provider(BaseProvider("function", "rstrip")):
    def exec(self, value, suffix=None):
        value = value.strip()
        if suffix and value.endswith(suffix):
            value = value[: -len(suffix)]
        return value
