from systems.plugins.index import BaseProvider


class Provider(BaseProvider('function', 'load_mock_data')):

    def exec(self, data_type):
        return self.load_data(data_type)['data']
