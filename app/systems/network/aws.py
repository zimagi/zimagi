from utility.cloud import AWSServiceMixin
from .base import *


class AWSNetworkProvider(AWSServiceMixin, NetworkProvider):
    
    def provider_config(self, type = None):
        super().provider_config(type)
        self.option(str, 'region', 'us-east-1', help = 'AWS region name', config_name = 'aws_region')
        self.option(str, 'tenancy', 'default', help = 'AWS VPC instance tenancy (default | dedicated)', config_name = 'aws_vpc_tenancy')
        self.option(bool, 'dns_support', True, help = 'AWS VPC DNS support', config_name = 'aws_vpc_dns_support')
        self.option(bool, 'dns_hostnames', False, help = 'AWS VPC DNS hostname assignment', config_name = 'aws_vpc_dns_hostnames')
  
    def initialize_terraform(self, instance, relations, created):
        self.aws_credentials(instance.config)
        super().initialize_terraform(instance, relations, created)

    def finalize_terraform(self, instance):
        self.aws_credentials(instance.config)
        super().finalize_terraform(instance)


class AWSNetworkPeerProvider(AWSServiceMixin, NetworkPeerProvider):
  
    def initialize_terraform(self, instance, relations, created, pair):
        namespace = self._peer_namespace(pair)
        source = pair[0]
        peer = pair[1]
        
        instance.config.setdefault(namespace, {})
        self.aws_credentials(instance.config[namespace])        
        
        try:
            instance.config[namespace]['region'] = source.config['region']
            instance.config[namespace]['vpc_id'] = source.variables['vpc_id']
            instance.config[namespace]['peer_region'] = peer.config['region']
            instance.config[namespace]['peer_vpc_id'] = peer.variables['vpc_id']
        
        except KeyError as e:
            self.command.warning("Could not access {} within {} peering connection".format(str(e), instance.name))

        super().initialize_terraform(instance, relations, created, pair)

    def finalize_terraform(self, instance, pair):
        namespace = self._peer_namespace(pair)

        instance.config.setdefault(namespace, {})
        self.aws_credentials(instance.config[namespace])
        
        super().finalize_terraform(instance, pair)


class AWSSubnetProvider(AWSServiceMixin, SubnetProvider):
    
    def provider_config(self, type = None):
        super().provider_config(type)
        self.option(str, 'zone', None, help = 'AWS availability zone (default random)', config_name = 'aws_zone')
        self.option(str, 'zone_suffix', None, help = 'AWS availability zone suffix (appended to region)', config_name = 'aws_zone_suffix')
        self.option(bool, 'public_ip', True, help = 'Enable public IP addresses for instances in subnet', config_name = 'aws_public_ip')

    def initialize_terraform(self, instance, relations, created):
        self.aws_credentials(instance.config)

        if instance.config['zone'] is None and instance.config['zone_suffix'] is not None:
            instance.config['zone'] = "{}{}".format(
                instance.network.config['region'], 
                instance.config['zone_suffix']
            )
        super().initialize_terraform(instance, relations, created)

    def finalize_terraform(self, instance):
        self.aws_credentials(instance.config)
        super().finalize_terraform(instance)
            

class AWSFirewallProvider(AWSServiceMixin, FirewallProvider):
  
    def initialize_terraform(self, instance, relations, created):
        self.aws_credentials(instance.config)
        super().initialize_terraform(instance, relations, created)

    def finalize_terraform(self, instance):
        self.aws_credentials(instance.config)
        super().finalize_terraform(instance)


class AWSFirewallRuleProvider(AWSServiceMixin, FirewallRuleProvider):
   
    def initialize_terraform(self, instance, relations, created):
        self.aws_credentials(instance.config)
        super().initialize_terraform(instance, relations, created)

    def finalize_terraform(self, instance):
        self.aws_credentials(instance.config)
        super().finalize_terraform(instance)


class AWS(BaseNetworkProvider):
    
    def register_types(self):
        super().register_types()
        self.set('network', AWSNetworkProvider)
        self.set('network_peer', AWSNetworkPeerProvider)
        self.set('subnet', AWSSubnetProvider)
        self.set('firewall', AWSFirewallProvider)
        self.set('firewall_rule', AWSFirewallRuleProvider)
