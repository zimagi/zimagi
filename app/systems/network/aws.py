from django.conf import settings

from utility.cloud import AWSServiceMixin
from .base import *

import random


class AWSNetworkProvider(AWSServiceMixin, NetworkProvider):
    
    def provider_config(self, type = None):
        super().provider_config(type)
        self.option(str, 'region', 'us-east-1', help = 'AWS region name', config_name = 'aws_region')
        self.option(str, 'tenancy', 'default', help = 'AWS VPC instance tenancy (default | dedicated)', config_name = 'aws_vpc_tenancy')
        self.option(bool, 'dns_support', False, help = 'AWS VPC DNS hostname support', config_name = 'aws_vpc_dns_support')
        self.option(bool, 'dns_hostnames', False, help = 'AWS VPC DNS hostname assignment', config_name = 'aws_vpc_dns_hostnames')

    def resource_variables(self):
        return {
            'vpc': 'aws_vpc.network',
            'internet_gateway': 'aws_internet_gateway.network',
            'route_table': 'aws_route_table.network',
            'gateway_route': 'aws_route.gateway'
        }
     
    def initialize_provider(self, instance, created):
        self.aws_credentials(instance.config)
        super().initialize_provider(instance, created)

    def finalize_provider(self, instance):
        self.aws_credentials(instance.config)
        super().finalize_provider(instance)
            

class AWSSubnetProvider(AWSServiceMixin, SubnetProvider):
    
    def provider_config(self, type = None):
        super().provider_config(type)
        self.option(str, 'zone', None, help = 'AWS availability zone (default random)', config_name = 'aws_zone')
        self.option(bool, 'public_ip', True, help = 'Enable public IP addresses for instances in subnet', config_name = 'aws_public_ip')

    def resource_variables(self):
        return {
            'subnet': 'aws_subnet.network'
        }
      
    def initialize_provider(self, instance, created):
        self.aws_credentials(instance.config)
        super().initialize_provider(instance, created)

    def finalize_provider(self, instance):
        self.aws_credentials(instance.config)
        super().finalize_provider(instance)
            

class AWSFirewallProvider(AWSServiceMixin, FirewallProvider):

    def resource_variables(self):
        return {
            'security_group': 'aws_security_group.firewall'
        }
    
    def initialize_provider(self, instance, created):
        self.aws_credentials(instance.config)
        super().initialize_provider(instance, created)

    def finalize_provider(self, instance):
        self.aws_credentials(instance.config)
        super().finalize_provider(instance)


class AWSFirewallRuleProvider(AWSServiceMixin, FirewallRuleProvider):
    
    def provider_config(self, type = None):
        self.option(str, 'mode', 'ingress', help = 'AWS security group rule type (ingress | egress)')
        self.option(str, 'protocol', 'tcp', help = 'AWS security group rule protocol (tcp | udp | icmp)')
        self.option(int, 'from_port', None, help = 'AWS security group rule from port (at least one "from" or "to" port must be specified)')
        self.option(int, 'to_port', None, help = 'AWS security group rule to port (at least one "from" or "to" port must be specified)')
        self.option(list, 'cidrs', [], help = 'AWS security group rule applicable CIDRs', config_name = 'aws_sgroup_cidrs')
    
    def initialize_provider(self, instance, created):
        self.aws_credentials(instance.config)
        
        instance.config['region'] = instance.firewall.config['region']
        instance.mode = instance.config['mode'].lower()
        instance.protocol = instance.config['protocol'].lower()
        instance.from_port = instance.config['from_port']
        instance.to_port = instance.config['to_port']

        if instance.mode not in ('ingress', 'egress'):
            self.command.error("Firewall rule mode {} is not supported".format(instance.type))
        
        if instance.protocol not in ('tcp', 'udp', 'icmp'):
            self.command.error("Firewall rule protocol {} is not supported".format(instance.protocol))

        if not instance.from_port and not instance.to_port:
            self.command.error("Either 'from' and 'to' port must be specified to create firewall")

        if not instance.from_port:
            instance.from_port = instance.to_port
        if not instance.to_port:
            instance.to_port = instance.from_port

        if instance.config['cidrs']:
            instance.cidrs = [str(self.parse_cidr(x.strip())) for x in instance.config['cidrs'].split(',')]
        else:
            instance.cidrs = ['0.0.0.0/0']
        
        instance.config['sgroup_id'] = instance.network.state['aws_security_group.firewall.id']
        super().initialize_provider(instance, created)

    def finalize_provider(self, instance):
        self.aws_credentials(instance.config)
        super().finalize_provider(instance)


class AWS(BaseNetworkProvider):
    
    def register_types(self):
        super().register_types()
        self.set('network', AWSNetworkProvider)
        self.set('subnet', AWSSubnetProvider)
        self.set('firewall', AWSFirewallProvider)
        self.set('firewall_rule', AWSFirewallRuleProvider)
