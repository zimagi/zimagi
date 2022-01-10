from systems.plugins.index import BasePlugin
from utility.data import Collection


class BaseProvider(BasePlugin('parser')):

    def __init__(self, type, name, command, config):
        super().__init__(type, name, command)
        self.config = config


    def initialize(self, reset = False):
        # Override in subclass
        pass

    def interpolate(self, data, options):
        def _interpolate(value):
            if value:
                if isinstance(value, (list, tuple)):
                    generated = []
                    for item in value:
                        item = _interpolate(item)
                        if item is not None:
                            generated.append(item)
                    value = generated
                elif isinstance(value, dict):
                    generated = {}
                    for key, item in value.items():
                        key = _interpolate(key)
                        if key is not None:
                            generated[key] = _interpolate(item)
                    value = generated
                else:
                    value = self.parse(value, Collection(**options))
            return value

        return _interpolate(data)

    def parse(self, value, config):
        # Override in subclass
        return value
