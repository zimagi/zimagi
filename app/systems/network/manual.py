from django.conf import settings

from .base import *


class ManualNetworkProvider(NetworkProvider):
    
    def provider_config(self, type = None):
        self.option(str, 'cidr', None, help = 'IPv4 CIDR address (between /16 and /28)')
        self.option(str, 'cidr_base', '10/8', help = 'IPv4 root CIDR address (not used if "cidr" option specified)')
        self.option(int, 'cidr_prefix', 16, help = 'IPv4 CIDR address prefix size (not used if "cidr" option specified)')

    def initialize_instance(self, instance, created, test):
        instance.cidr = self.get_cidr(instance.config, self.command.networks)
        if not instance.cidr:
            self.command.error("No available network cidr matches. Try another cidr")


class ManualSubnetProvider(SubnetProvider):
    
    def provider_config(self, type = None):
        self.option(str, 'cidr', None, help = 'IPv4 CIDR address (between /16 and /28)')
        self.option(int, 'cidr_prefix', 24, help = 'IPv4 CIDR address prefix size (not used if "cidr" option specified)')

    def initialize_instance(self, instance, created, test):
        instance.config['cidr_base'] = instance.network.cidr
        instance.cidr = self.get_cidr(instance.config, self.command.subnets)
        if not instance.cidr:
            self.command.error("No available subnet cidr matches. Try another cidr")


class Manual(BaseNetworkProvider):
    
    def register_types(self):
        super().register_types()
        self.set('network', ManualNetworkProvider)
        self.set('subnet', ManualSubnetProvider)
