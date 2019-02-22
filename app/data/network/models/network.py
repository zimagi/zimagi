from systems import models
from systems.models import environment, provider


class NetworkFacade(
    provider.ProviderModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    pass


class Network(
    provider.ProviderMixin,
    environment.EnvironmentModel
):
    cidr = models.CharField(null=True, max_length=128)

    class Meta:
        facade_class = NetworkFacade

    def get_provider_name(self):
        return 'network:network'
