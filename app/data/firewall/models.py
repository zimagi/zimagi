from django.db import models as django

from systems.models import network, provider


class FirewallFacade(
    provider.ProviderModelFacadeMixin,
    network.NetworkModelFacadeMixin
):
    pass


class Firewall(
    provider.ProviderMixin,
    network.NetworkModel
):
    class Meta(network.NetworkModel.Meta):
        facade_class = FirewallFacade

    def __str__(self):
        return "{}".format(self.name)

    def get_provider_name(self):
        return 'network:firewall'
