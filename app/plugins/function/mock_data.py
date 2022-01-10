from systems.plugins.index import BaseProvider
from utility.filesystem import load_yaml


class Provider(BaseProvider('function', 'mock_data')):

    def exec(self, type):
        data_file = self.manager.index.get_module_file("tests/data/{}.yml".format(type))
        return load_yaml(data_file)
