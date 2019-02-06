from django.conf import settings

from systems.command import providers

import netaddr
import ipaddress


class SubnetMixin(object):

    def get_cidr(self, instance, config, networks):
        if config['cidr']:
            cidrs = [self.parse_cidr(config['cidr'])]
        else:
            cidrs = self.parse_subnets(
                config['cidr_base'], 
                config['cidr_prefix']
            )
        
        for cidr in cidrs:
            create = True

            for network in networks:
                if instance.name != network.name:
                    if network.cidr and self.overlapping_subnets(cidr, network.cidr):
                        create = False
                        break
            
            if create:
                return str(cidr)
        
        return None

    def parse_cidr(self, cidr):
        cidr = str(cidr)

        if '*' in cidr or '-' in cidr:
            return netaddr.glob_to_cidrs(cidr)[0]
        
        if '/' not in cidr:
            cidr = "{}/32".format(cidr)
        
        return netaddr.IPNetwork(cidr, implicit_prefix = True)

    def parse_subnets(self, cidr, prefix_size):
        return list(self.parse_cidr(str(cidr)).subnet(int(prefix_size)))

    def overlapping_subnets(self, cidr, other_cidr):
        cidr1 = ipaddress.IPv4Network(str(cidr))
        cidr2 = ipaddress.IPv4Network(str(other_cidr))
        return cidr1.overlaps(cidr2)


class NetworkProvider(SubnetMixin, providers.TerraformProvider):
    
    def provider_config(self, type = None):
        self.option(str, 'cidr', None, help = 'Network IPv4 CIDR address (between /16 and /28)')
        self.option(str, 'cidr_base', '10/8', help = 'Network IPv4 root CIDR address (not used if "cidr" option specified)')
        self.option(int, 'cidr_prefix', 16, help = 'Network IPv4 CIDR address prefix size (not used if "cidr" option specified)')
    
    def terraform_type(self):
        return 'network'

    @property
    def facade(self):
        return self.command._network

    def create(self, name, fields, test = False):
        fields['type'] = self.name
        return super().create(name, fields, test)
     
    def initialize_provider(self, instance, created):
        instance.cidr = self.get_cidr(instance, self.config, self.command.networks)
        if not instance.cidr:
            self.command.error("No available network cidr matches. Try another cidr")
         

class SubnetProvider(SubnetMixin, providers.TerraformProvider):
    
    def provider_config(self, type = None):
        self.option(str, 'cidr', None, help = 'Network IPv4 CIDR address (between /16 and /28)')
        self.option(int, 'cidr_prefix', 16, help = 'Network IPv4 CIDR address prefix size (not used if "cidr" option specified)')

    def terraform_type(self):
        return 'subnet'

    @property
    def facade(self):
        return self.command._subnet

    def create(self, name, network, fields, test = False):
        fields['type'] = self.name
        fields['network'] = network
        return super().create(name, fields, test)
    
    def initialize_provider(self, instance, created):
        self.config['cidr_base'] = instance.network.cidr
        instance.cidr = self.get_cidr(instance, self.config, self.command.subnets)
        if not instance.cidr:
            self.command.error("No available subnet cidr matches. Try another cidr")


class FirewallProvider(providers.TerraformProvider):

    def terraform_type(self):
        return 'firewall'

    @property
    def facade(self):
        return self.command._firewall

    def create(self, name, network, fields, test = False):
        fields['type'] = self.name
        fields['network'] = network
        return super().create(name, fields, test)


class FirewallRuleProvider(providers.TerraformProvider):

    def terraform_type(self):
        return 'firewall_rule'

    @property
    def facade(self):
        return self.command._firewall_rule

    def create(self, name, firewall, fields, test = False):
        fields['type'] = self.name
        fields['firewall'] = firewall
        return super().create(name, fields, test)


class BaseNetworkProvider(providers.MetaCommandProvider):

    def __init__(self, name, command, instance = None):
        super().__init__(name, command, instance)
        self.provider_type = 'network'
        self.provider_options = settings.NETWORK_PROVIDERS
    
    def register_types(self):
        self.set('network', NetworkProvider)
        self.set('subnet', SubnetProvider)
        self.set('firewall', FirewallProvider)
        self.set('firewall_rule', FirewallRuleProvider)
