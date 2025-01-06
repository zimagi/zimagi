from systems.plugins.index import BasePlugin


class BaseProvider(BasePlugin("field_processor")):
    def exec(self, dataset, field_data):
        # Override in subclass
        return field_data
