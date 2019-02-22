from systems import models

from data.network import models as network
from .resource import ResourceModel, ResourceModelFacadeMixin


class NetworkModelFacadeMixin(ResourceModelFacadeMixin):

    def set_scope(self, network):
        super().set_scope(network_id = network.id)


class NetworkMixin(object):
    
    network = models.ForeignKey(network.Network, on_delete=models.PROTECT)


class NetworkModel(NetworkMixin, ResourceModel):

    class Meta:
        abstract = True
        unique_together = ('network', 'name')

    def __str__(self):
        return "{}:{}".format(self.network.name, self.name)

    def get_id_fields(self):
        return ('name', 'network_id')
