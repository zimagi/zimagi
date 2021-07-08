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
                    for index, item in enumerate(value):
                        value[index] = _interpolate(value[index])
                elif isinstance(value, dict):
                    items = {}
                    for key, item in value.items():
                        items[_interpolate(key)] = _interpolate(value[key])
                    value = items
                else:
                    value = self.parse(value, Collection(**options))
            return value

        return _interpolate(data)

    def parse(self, value, config):
        # Override in subclass
        return value
