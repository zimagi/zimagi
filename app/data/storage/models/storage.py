from systems import models
from systems.models import network, provider


class StorageFacade(
    provider.ProviderModelFacadeMixin,
    network.NetworkModelFacadeMixin
):
    pass


class Storage(
    provider.ProviderMixin,
    network.NetworkModel
):
    class Meta:
        facade_class = StorageFacade

    def __str__(self):
        return "{}".format(self.name)

    def get_provider_name(self):
        return 'storage:storage'
