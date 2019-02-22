from systems import models

from data.network import models as network
from .resource import ResourceModel, ResourceModelFacadeMixin


class SubnetModelFacadeMixin(ResourceModelFacadeMixin):

    def set_scope(self, subnet):
        super().set_scope(subnet_id = subnet.id)


class SubnetMixin(object):
    
    subnet = models.ForeignKey(network.Subnet, on_delete=models.PROTECT)


class SubnetModel(SubnetMixin, ResourceModel):

    class Meta:
        abstract = True
        unique_together = ('subnet', 'name')

    def __str__(self):
        return "{}:{}".format(self.subnet.name, self.name)

    def get_id_fields(self):
        return ('name', 'subnet_id')
