from django.conf import settings

from systems.command import providers

import netaddr
import ipaddress
import threading


class NetworkResult(object):

    def __init__(self, type, config,
        cidr = None
    ):
        self.type = type
        self.config = config
        self.cidr = cidr

    def __str__(self):
        return "[{}]> ({})".format(
            self.type,
            self.cidr      
        )

class SubnetResult(object):

    def __init__(self, config,
        cidr = None
    ):
        self.config = config
        self.cidr = cidr

    def __str__(self):
        return "({})".format(
            self.cidr      
        )

class FirewallResult(object):

    def __init__(self, name, config,
        description = None
    ):
        self.name = name
        self.config = config
        self.description = description

    def __str__(self):
        return "{}".format(
            self.name     
        )

class FirewallRuleResult(object):

    def __init__(self, name, config,
        type = None,
        from_port = None,
        to_port = None,
        protocol = None,
        cidrs = None
    ):
        self.name = name
        self.config = config
        self.type = type
        self.from_port = from_port
        self.to_port = to_port
        self.protocol = protocol
        self.cidrs = cidrs

    def __str__(self):
        return "{} ({})".format(
            self.name,
            self.type    
        )


class BaseNetworkProvider(providers.BaseCommandProvider):

    def __init__(self, name, command, network = None):
        super().__init__(name, command)

        self.network = network
        self.thread_lock = threading.Lock()

        self.provider_type = 'network'
        self.provider_options = settings.NETWORK_PROVIDERS


    def create_network(self, config):
        self.config = config
        
        self.provider_config('network')
        self.validate()

        network = NetworkResult(self.name, config)

        for key, value in self.config.items():
            if hasattr(network, key) and key not in ('type', 'config'):
                setattr(network, key, value)

        self.initialize_network(network)
        return network

    def initialize_network(self, network):
        # Override in subclass
        pass

    def destroy_network(self):
        # Override in subclass
        pass


    def create_subnet(self, config):
        self.config = config
        
        self.provider_config('subnet')
        self.validate()

        subnet = SubnetResult(config)

        for key, value in self.config.items():
            if hasattr(subnet, key) and key not in ('config',):
                setattr(subnet, key, value)

        self.initialize_subnet(subnet)
        return subnet

    def initialize_subnet(self, subnet):
        # Override in subclass
        pass

    def destroy_subnet(self, subnet):
        # Override in subclass
        pass


    def create_firewall(self, name, config):
        self.config = config
        
        self.provider_config('firewall')
        self.validate()

        firewall = FirewallResult(name, config)

        for key, value in self.config.items():
            if hasattr(firewall, key) and key not in ('config',):
                setattr(firewall, key, value)

        self.initialize_firewall(name, firewall)
        return firewall

    def initialize_firewall(self, name, firewall):
        # Override in subclass
        pass

    def destroy_firewall(self, firewall):
        # Override in subclass
        pass


    def create_firewall_rule(self, firewall, name, config):
        self.config = config
        
        self.provider_config('firewall_rule')
        self.validate()

        rule = FirewallRuleResult(name, config)

        for key, value in self.config.items():
            if hasattr(rule, key) and key not in ('config',):
                setattr(rule, key, value)

        self.initialize_firewall_rule(firewall, name, rule)
        return rule

    def initialize_firewall_rule(self, firewall, name, rule):
        # Override in subclass
        pass

    def destroy_firewall_rule(self, firewall, rule):
        # Override in subclass
        pass


    def _get_cidr(self, config, networks):
        if config['cidr']:
            cidrs = [config['cidr']]
        else:
            cidrs = self._parse_subnets(
                config['cidr_base'], 
                config['cidr_prefix']
            )
        
        for cidr in cidrs:
            create = True

            for network in networks:
                if self._overlapping_subnets(cidr, network.cidr):
                    create = False
                    break
            
            if create:
                return str(cidr)
        
        return None

    def _parse_cidr(self, cidr):
        cidr = str(cidr)

        if '*' in cidr or '-' in cidr:
            return netaddr.glob_to_cidrs(cidr)[0]
        
        if '/' not in cidr:
            cidr = "{}/32".format(cidr)
        
        return netaddr.IPNetwork(cidr, implicit_prefix = True)

    def _parse_subnets(self, cidr, prefix_size):
        return list(self._parse_cidr(str(cidr)).subnet(int(prefix_size)))

    def _overlapping_subnets(self, cidr, other_cidr):
        cidr1 = ipaddress.IPv4Network(str(cidr))
        cidr2 = ipaddress.IPv4Network(str(other_cidr))
        return cidr1.overlaps(cidr2)
