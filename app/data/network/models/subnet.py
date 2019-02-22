from systems import models
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
    cidr = models.CharField(null=True, max_length=128)

    class Meta:
        facade_class = SubnetFacade

    def __str__(self):
        return "{} ({})".format(self.name, self.cidr)

    def get_provider_name(self):
        return 'network:subnet'
