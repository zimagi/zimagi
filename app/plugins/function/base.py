from systems.plugins.index import BasePlugin


class BaseProvider(BasePlugin('function')):

    def exec(self, *parameters):
        # Override in subclass
        return None
