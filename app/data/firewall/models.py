from django.db import models as django

from systems.models import group, network, provider


class FirewallFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    network.NetworkModelFacadeMixin
):
    def get_provider_name(self):
        return 'network:firewall'
    
    def get_relations(self):
        return {
            'groups': ('group', 'group_names', '--groups')
        }


class Firewall(
    provider.ProviderMixin,
    group.GroupMixin,
    network.NetworkModel
):
    class Meta(network.NetworkModel.Meta):
        facade_class = FirewallFacade

    def __str__(self):
        return "{}".format(self.name)
