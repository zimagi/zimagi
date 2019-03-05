from django.conf import settings

from data.network.models import Network
from data.subnet.models import Subnet
from systems.command import providers

import netaddr
import ipaddress
import itertools
import threading


class AddressMap(object):

    def __init__(self):
        self.cidr_index = {}
        self.thread_lock = threading.Lock()


    def cidr(self, config):
        with self.thread_lock:
            if config['cidr']:
                cidrs = [self.parse_cidr(config['cidr'])]
            else:
                cidrs = self.parse_subnets(
                    config['cidr_base'], 
                    config['cidr_prefix']
                )
        
            for cidr in cidrs:
                create = True

                for indexed_cidr in self.cidr_index.keys():
                    if self.overlapping_subnets(cidr, indexed_cidr):
                        create = False
                        break
            
                if create:
                    cidr = str(cidr)
                    self.cidr_index[cidr] = True
                    return cidr
        
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


class NetworkAddressMap(AddressMap):
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        if not getattr(self, '_initialized', False):
            super().__init__()

            with self.thread_lock:
                for network in Network.facade.all():
                    self.cidr_index[network.cidr] = True
        
            self._initialized = True


class SubnetAddressMap(AddressMap):
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        if not getattr(self, '_initialized', False):
            super().__init__()

            with self.thread_lock:
                for subnet in Subnet.facade.all():
                    self.cidr_index[subnet.cidr] = True
        
            self._initialized = True


class NetworkMixin(object):

    @property    
    def address(self):
        return NetworkAddressMap()

class SubnetMixin(object):

    @property    
    def address(self):
        return SubnetAddressMap()


class NetworkProvider(NetworkMixin, providers.TerraformProvider):
    
    def provider_config(self, type = None):
        self.option(str, 'cidr', None, help = 'Network IPv4 CIDR address (between /16 and /28)')
        self.option(str, 'cidr_base', '10/8', help = 'Network IPv4 root CIDR address (not used if "cidr" option specified)')
        self.option(int, 'cidr_prefix', 16, help = 'Network IPv4 CIDR address prefix size (not used if "cidr" option specified)')
    
    def terraform_type(self):
        return 'network'

    @property
    def facade(self):
        return self.command._network
     
    def initialize_terraform(self, instance, created):
        if not instance.cidr:
            instance.cidr = self.address.cidr(self.config)
        
        if not instance.cidr:
            self.command.error("No available network cidr matches. Try another cidr")


class SubnetProvider(SubnetMixin, providers.TerraformProvider):
    
    def provider_config(self, type = None):
        self.option(str, 'cidr', None, help = 'Subnet IPv4 CIDR address (between /16 and /28)')
        self.option(int, 'cidr_prefix', 24, help = 'Subnet IPv4 CIDR address prefix size (not used if "cidr" option specified)')

    def terraform_type(self):
        return 'subnet'

    @property
    def facade(self):
        return self.command._subnet
     
    def initialize_terraform(self, instance, created):
        self.config['cidr_base'] = instance.network.cidr

        if not instance.cidr:
            instance.cidr = self.address.cidr(self.config)

        if not instance.cidr:
            self.command.error("No available subnet cidr matches. Try another cidr")


class FirewallProvider(providers.TerraformProvider):

    def terraform_type(self):
        return 'firewall'

    @property
    def facade(self):
        return self.command._firewall


class FirewallRuleProvider(NetworkMixin, providers.TerraformProvider):
    
    def provider_config(self, type = None):
        self.option(str, 'mode', 'ingress', help = 'Firewall rule mode (ingress | egress)')
        self.option(str, 'protocol', 'tcp', help = 'Firewall rule protocol (tcp | udp | icmp | all)')
        self.option(int, 'from_port', 0, help = 'Firewall rule from port')
        self.option(int, 'to_port', 65535, help = 'Firewall rule to port')
        self.option(list, 'cidrs', [], help = 'Firewall rule applicable CIDRs')

    def terraform_type(self):
        return 'firewall_rule'

    @property
    def facade(self):
        return self.command._firewall_rule
        
    def initialize_terraform(self, instance, created):
        if instance.mode not in ('ingress', 'egress'):
            self.command.error("Firewall rule mode {} is not supported".format(instance.type))
        
        if instance.protocol not in ('tcp', 'udp', 'icmp', 'all'):
            self.command.error("Firewall rule protocol {} is not supported".format(instance.protocol))

        if instance.cidrs:
            instance.cidrs = [str(self.address.parse_cidr(x.strip())) for x in instance.cidrs]
        else:
            instance.cidrs = ['0.0.0.0/0']


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
