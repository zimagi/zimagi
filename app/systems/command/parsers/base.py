
class ParserBase(object):

    def __init__(self, command):
        self.command = command


    def initialize(self, reset = False):
        # Override in subclass
        pass

    def interpolate(self, data):
        def _interpolate(value):
            if value:
                if isinstance(value, (list, tuple)):
                    for index, item in enumerate(value):
                        value[index] = _interpolate(value[index])
                elif isinstance(value, dict):
                    for key, item in value.items():
                        value[key] = _interpolate(value[key])
                else:
                    value = self.parse(value)
            return value

        return _interpolate(data)

    def parse(self, value):
        # Override in subclass
        return value