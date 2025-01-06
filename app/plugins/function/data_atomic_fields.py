from systems.plugins.index import BaseProvider


class Provider(BaseProvider("function", "data_atomic_fields")):
    def exec(self, data_type):
        facade = self.command.facade(data_type)
        return facade.atomic_fields
