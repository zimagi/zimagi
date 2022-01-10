from systems.plugins.index import BaseProvider


class Provider(BaseProvider('function', 'data_key')):

    def exec(self, data_type):
        facade = self.command.facade(data_type)
        return facade.key()
