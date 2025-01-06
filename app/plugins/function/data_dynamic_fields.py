from systems.plugins.index import BaseProvider


class Provider(BaseProvider("function", "data_dynamic_fields")):
    def exec(self, data_type):
        facade = self.command.facade(data_type)
        return facade.dynamic_fields
