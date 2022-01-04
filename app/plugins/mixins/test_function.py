from systems.plugins.index import ProviderMixin
from utility.filesystem import load_yaml


class TestFunctionMixin(ProviderMixin('test_function')):

    def load_data(self, data_type):
        if not getattr(self, '_data_files', None):
            self._data_files = {}

        if data_type not in self._data_files:
            data_file = self.manager.index.get_module_file("tests/data/{}.yml".format(data_type))
            self._data_files[data_type] = load_yaml(data_file)
        return self._data_files[data_type]
