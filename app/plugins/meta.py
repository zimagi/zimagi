from plugins import base
from systems.plugins import index as plugin_index


class MetaProviderAccessError(Exception):
    pass


class BasePlugin(base.BasePlugin):

    @classmethod
    def generate(cls, plugin, generator):
        super().generate(plugin, generator)

        if 'subtypes' not in generator.spec:
            raise base.GeneratorError("Specification 'subtypes' not present in {} plugin definition".format(generator.name))

        def register_types(self):
            for subtype, spec in generator.spec['subtypes'].items():
                self.set(subtype, plugin_index.BasePlugin(subtype,
                    base_class_name = "{}MetaProvider".format(subtype.title())
                    module_path = generator.module_path,
                    spec = spec
                ))

        plugin.register_types = register_types


    def __init__(self, type, name, command, *args, **options):
        super().__init__(type, name, command)
        self.provider_index = {}
        self.register_types()
        self.args = args
        self.options = options

    def register_types(self):
        # Override in subclass
        pass


    def context(self, subtype, test = False):
        if subtype is None:
            return super().context(subtype, test)

        provider = self.provider(subtype)(
            self.provider_type,
            self.name,
            self.command,
            *self.args,
            **self.options
        )
        provider.test = test
        return provider


    def provider_schema(self, type):
        provider = self.context(type, self.test)
        return provider.provider_schema()


    def __getattr__(self, type):
        return self.context(type, self.test)

    def provider(self, type):
        if type in self.provider_index:
            return self.provider_index[type]
        else:
            raise MetaProviderAccessError("Sub provider {} does not exist in {} index".format(type, self.name))


    def set(self, type, provider_cls):
        self.provider_index[type] = provider_cls
