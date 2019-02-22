from systems import models
from systems.models import environment, provider
from data.network import models as network


class FederationFacade(
    provider.ProviderModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    pass


class Federation(
    provider.ProviderMixin,
    environment.EnvironmentModel
):
    networks = models.ManyToManyField(network.Network)    
    
    class Meta:
        facade_class = FederationFacade

    def get_provider_name(self):
        return 'federation'
