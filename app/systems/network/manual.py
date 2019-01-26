from django.conf import settings

from .base import BaseNetworkProvider


class Manual(BaseNetworkProvider):

    def provider_config(self, type = None):
        if type:
            if type == 'network':
                self.option('cidr', None, help = 'IPv4 CIDR address (between /16 and /28)')
                self.option('cidr_base', '10/8', help = 'IPv4 root CIDR address (not used if "cidr" option specified)')
                self.option('cidr_prefix', '16', help = 'IPv4 CIDR address prefix size (not used if "cidr" option specified)')
            
            elif type == 'subnet':
                self.option('cidr', None, help = 'IPv4 CIDR address (between /16 and /28)')
                self.option('cidr_prefix', '24', help = 'IPv4 CIDR address prefix size (not used if "cidr" option specified)')
            
            elif type == 'firewall':
                pass
            
            elif type == 'firewall_rule':
                pass
             
            else:
                self.command.error("Network option type {} is unsupported in manual network provider".format(type))
        else:
            self.command.error("Network option type must be specified to use manual network provider")


    def initialize_network(self, network):
        network.cidr = self._get_cidr(self.config, self.command.networks)
        if not network.cidr:
            self.command.error("No available network cidr matches. Try another cidr")
        

    def initialize_subnet(self, subnet):
        if not self.network:
            self.command.error("Creating subnet requires a valid network instance given to provider on initialization")
        
        self.config['cidr_base'] = self.network.cidr
        subnet.cidr = self._get_cidr(self.config, self.command.subnets)
        if not subnet.cidr:
            self.command.error("No available subnet cidr matches. Try another cidr")
