from systems.models.index import ModelMixin, ModelMixinFacade


class ProviderMixinFacadeOverride(ModelMixinFacade('provider')):

    @property
    def provider_name(self):
        if getattr(self.meta, 'provider_name', None):
            return self.meta.provider_name
        return None

    @property
    def provider_relation(self):
        if getattr(self.meta, 'provider_relation', None):
            return self.meta.provider_relation
        return None


class ProviderMixinOverride(ModelMixin('provider')):

    def initialize(self, command):
        if not super().initialize(command):
            return False

        provider_name = self.facade.provider_name
        if provider_name:
            self.provider = command.get_provider(provider_name, self.provider_type, instance = self)
        return True
