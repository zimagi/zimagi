from django.db import models as django

from systems.models import environment, group, network, provider


class FederationFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    def get_provider_name(self):
        return 'federation'
    
    def get_relations(self):
        return {
            'groups': ('group', 'Groups', '--groups')
        }


class Federation(
    provider.ProviderMixin,
    network.NetworkRelationMixin,
    group.GroupMixin,
    environment.EnvironmentModel
):
    class Meta(environment.EnvironmentModel.Meta):
        facade_class = FederationFacade
