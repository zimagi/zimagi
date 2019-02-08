from .base import BaseCommandProvider


class MetaProviderAccessError(Exception):
    pass


class MetaCommandProvider(BaseCommandProvider):

    def __init__(self, name, command, instance = None):
        super().__init__(name, command, instance)
        self.provider_index = {}
        self.register_types()

    def register_types(self):
        # Override in subclass
        pass


    def context(self, type, test = False):
        if type is None:
            return super().context(type, test)
        
        provider = self.provider(type)(
            self.name,
            self.command,
            self.instance
        )
        provider.test = test
        return provider


    def provider_schema(self, type):
        provider = self.context(type, self.test)
        return provider.provider_schema()

    def field_help(self, type):
        return super().field_help(type)


    def __getattr__(self, type):
        return self.context(type, self.test)

    def provider(self, type):
        if type in self.provider_index:
            return self.provider_index[type]
        else:
            raise MetaProviderAccessError("Sub provider {} does not exist in {} index".format(type, self.name))


    def set(self, type, provider_cls):
        self.provider_index[type] = provider_cls
