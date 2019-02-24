from django.db import models as django

from systems.models import network, provider


class SubnetFacade(
    provider.ProviderModelFacadeMixin,
    network.NetworkModelFacadeMixin
):
    pass


class Subnet(
    provider.ProviderMixin,
    network.NetworkModel
):
    cidr = django.CharField(null=True, max_length=128)

    class Meta(network.NetworkModel.Meta):
        facade_class = SubnetFacade

    def __str__(self):
        return "{} ({})".format(self.name, self.cidr)

    def get_provider_name(self):
        return 'network:subnet'
