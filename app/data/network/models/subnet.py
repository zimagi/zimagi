from systems import models
from data.environment import models as env
from data.network import models as network

import netaddr
import json


class SubnetFacade(models.ConfigModelFacade):

    def get_packages(self):
        return super().get_packages() + ['network', 'server']


    def key(self):
        return 'name'


    def scope(self, fields = False):
        if fields:
            return ('environment',)
        
        curr_env = env.Environment.facade.get_env()
        if not curr_env:
            return False

        return { 'environment_id': curr_env }

    def set_scope(self, network):
        super().set_scope(network_id = network.id)


class Subnet(models.AppConfigModel):

    name = models.CharField(max_length=128)
    cidr = models.CharField(null=True, max_length=128)
    
    environment = models.ForeignKey(env.Environment, related_name='subnets', on_delete=models.CASCADE)
    network = models.ForeignKey(network.Network, related_name='subnets', on_delete=models.CASCADE)

    @property
    def cidr_prefix_size(self):
        ip_space = netaddr.IPNetwork(self.cidr)
        return ip_space.prefixlen


    class Meta:
        unique_together = (
            ('environment', 'name'),
            ('network', 'name')
        )
        facade_class = SubnetFacade


    def __str__(self):
        return "{} ({})".format(self.name, self.cidr)
