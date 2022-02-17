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
        options = Collection(**options)

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
                            item = _interpolate(item)

                            if isinstance(key, dict):
                                for sub_key, sub_value in key.items():
                                    generated[sub_key] = sub_value if sub_value is not None else item
                            elif isinstance(key, (list, tuple)):
                                for sub_key in key:
                                    generated[sub_key] = item
                            else:
                                generated[key] = item
                    value = generated
                else:
                    value = self.parse(value, options)
            return value

        return _interpolate(data)

    def parse(self, value, config):
        # Override in subclass
        return value
