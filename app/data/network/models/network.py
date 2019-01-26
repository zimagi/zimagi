from systems import models
from data.environment import models as env

import netaddr
import json


class NetworkFacade(models.ConfigModelFacade):

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


class Network(models.AppConfigModel):

    name = models.CharField(max_length=128)
    cidr = models.CharField(null=True, max_length=128)
    type = models.CharField(null=True, max_length=128)
    
    environment = models.ForeignKey(env.Environment, related_name='networks', on_delete=models.CASCADE)

    @property
    def cidr_prefix_size(self):
        ip_space = netaddr.IPNetwork(self.cidr)
        return ip_space.prefixlen


    class Meta:
        unique_together = ('environment', 'name')
        facade_class = NetworkFacade


    def __str__(self):
        return "{} ({})".format(self.name, self.cidr)


    def initialize(self, command):
        self.provider = command.get_provider('network', self.type, network = self)
        return True


    def get_subnets(self, subnet_prefix_size):
        ip_space = netaddr.IPNetwork(self.cidr)
        return list(ip_space.subnet(subnet_prefix_size))
