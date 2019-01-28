from systems import models
from data.network import models as network

import json
import re


class FirewallFacade(models.ConfigModelFacade):

    def get_packages(self):
        return super().get_packages() + ['network', 'server']

    def key(self):
        return 'name'

    def set_scope(self, network):
        super().set_scope(network_id = network.id)


class Firewall(models.AppConfigModel):

    name = models.CharField(max_length=128)
    
    network = models.ForeignKey(network.Network, related_name='firewalls', on_delete=models.PROTECT)
   
    class Meta:
        unique_together = (
            ('network', 'name')
        )
        facade_class = FirewallFacade


    def __str__(self):
        return "{}".format(self.name)
