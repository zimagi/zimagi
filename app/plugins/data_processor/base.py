from systems.plugins.index import BasePlugin


class BaseProvider(BasePlugin('data_processor')):

    def exec(self, dataset):
        # Override in subclass
        return dataset
