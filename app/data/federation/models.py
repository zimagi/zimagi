from django.db import models as django

from systems.models import environment, network, provider


class FederationFacade(
    provider.ProviderModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    pass


class Federation(
    provider.ProviderMixin,
    network.NetworkRelationMixin,
    environment.EnvironmentModel
):
    class Meta(environment.EnvironmentModel.Meta):
        facade_class = FederationFacade

    def get_provider_name(self):
        return 'federation'
