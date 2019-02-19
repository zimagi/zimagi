from django.conf import settings

from data.network import models
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
                for network in models.Network.facade.all():
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
                for subnet in models.Subnet.facade.all():
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

    def create(self, name, fields):
        fields['type'] = self.name
        return super().create(name, fields)
     
    def initialize_terraform(self, instance, relations, created):
        if not instance.cidr:
            instance.cidr = self.address.cidr(self.config)
        
        if not instance.cidr:
            self.command.error("No available network cidr matches. Try another cidr")


class NetworkPeerProvider(providers.TerraformProvider):
   
    def terraform_type(self):
        return 'network_peer'

    @property
    def facade(self):
        return self.command._network_peer

    def create(self, name, peer_names):
        return super().create(name, { 'type': self.name }, peers = peer_names)

    def update(self, peer_names):
        return super().update({}, peers = peer_names)
      
    def initialize_instance(self, instance, relations, created):
        instance.save()

        self.update_related(instance, 'peers', self.command._network, relations['peers'])
        peer_map, peer_pairs = self._load_peers(list(instance.peers.all()))

        def process(pair_names, state):
            pair = (peer_map[pair_names[0]], peer_map[pair_names[1]])
            namespace = self._peer_namespace(pair)

            self.initialize_terraform(instance, relations, created, pair)

            if self.test:
                self.terraform.plan(self.terraform_type(), instance, namespace)
            else:
                self.terraform.apply(self.terraform_type(), instance, namespace)

        self.command.run_list(peer_pairs, process)

    def finalize_instance(self, instance):
        peer_map, peer_pairs = self._load_peers(list(instance.peers.all()))

        def process(pair_names, state):
            pair = (peer_map[pair_names[0]], peer_map[pair_names[1]])
            
            self.finalize_terraform(instance, pair)
            self.terraform.destroy(
                self.terraform_type(), 
                instance, 
                self._peer_namespace(pair)
            )
        self.command.run_list(peer_pairs, process)


    def _load_peers(self, peers):
        peer_names = []
        peer_map = {}
        
        for peer in peers:
            peer_names.append(peer.name)
            peer_map[peer.name] = peer
        
        peer_pairs = list(itertools.combinations(peer_names, 2))
        return (peer_map, peer_pairs)

    def _peer_namespace(self, pair):
        return "{}.{}".format(pair[0].name, pair[1].name)


class SubnetProvider(SubnetMixin, providers.TerraformProvider):
    
    def provider_config(self, type = None):
        self.option(str, 'cidr', None, help = 'Subnet IPv4 CIDR address (between /16 and /28)')
        self.option(int, 'cidr_prefix', 24, help = 'Subnet IPv4 CIDR address prefix size (not used if "cidr" option specified)')

    def terraform_type(self):
        return 'subnet'

    @property
    def facade(self):
        return self.command._subnet

    def create(self, name, network, fields):
        fields['type'] = self.name
        fields['network'] = network
        return super().create(name, fields)
    
    def initialize_terraform(self, instance, relations, created):
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

    def create(self, name, network, fields):
        fields['type'] = self.name
        fields['network'] = network
        return super().create(name, fields)


class FirewallRuleProvider(NetworkMixin, providers.TerraformProvider):
    
    def provider_config(self, type = None):
        self.option(str, 'mode', 'ingress', help = 'Firewall rule mode (ingress | egress)')
        self.option(str, 'protocol', 'tcp', help = 'Firewall rule protocol (tcp | udp | icmp | all)')
        self.option(int, 'from_port', 0, help = 'Firewall rule from port')
        self.option(int, 'to_port', 65535, help = 'Firewall rule to port')
        self.option(list, 'cidrs', [], help = 'Firewall rule applicable CIDRs', config_name = 'aws_sgroup_cidrs')

    def terraform_type(self):
        return 'firewall_rule'

    @property
    def facade(self):
        return self.command._firewall_rule

    def create(self, name, firewall, fields):
        fields['type'] = self.name
        fields['firewall'] = firewall
        return super().create(name, fields)
        
    def initialize_terraform(self, instance, relations, created):
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
        self.set('network_peer', NetworkPeerProvider)
        self.set('subnet', SubnetProvider)
        self.set('firewall', FirewallProvider)
        self.set('firewall_rule', FirewallRuleProvider)
