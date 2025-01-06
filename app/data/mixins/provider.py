from systems.models.index import ModelMixin, ModelMixinFacade


class ProviderMixinFacade(ModelMixinFacade("provider")):
    @property
    def provider_name(self):
        if getattr(self.meta, "provider_name", None):
            return self.meta.provider_name
        return None


class ProviderMixin(ModelMixin("provider")):
    def initialize(self, command, facade=None, **options):
        if not super().initialize(command, **options):
            return False

        provider_name = self.facade.provider_name
        if provider_name:
            self.provider = command.get_provider(provider_name, self.provider_type, instance=self, facade=facade)
        return True
