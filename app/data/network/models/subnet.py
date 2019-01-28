from systems import models
from data.network import models as network

import netaddr
import json


class SubnetFacade(models.ConfigModelFacade):

    def get_packages(self):
        return super().get_packages() + ['network', 'server']

    def key(self):
        return 'name'

    def set_scope(self, network):
        super().set_scope(network_id = network.id)


class Subnet(models.AppConfigModel):

    name = models.CharField(max_length=128)
    cidr = models.CharField(null=True, max_length=128)
    
    network = models.ForeignKey(network.Network, related_name='subnets', on_delete=models.PROTECT)

    @property
    def cidr_prefix_size(self):
        ip_space = netaddr.IPNetwork(self.cidr)
        return ip_space.prefixlen


    class Meta:
        unique_together = (
            ('network', 'name')
        )
        facade_class = SubnetFacade


    def __str__(self):
        return "{} ({})".format(self.name, self.cidr)
