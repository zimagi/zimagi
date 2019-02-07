from utility.cloud import AWSServiceMixin
from .base import *


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

    def resource_variables(self):
        return {
            'security_group_rule': 'aws_security_group_rule.firewall'
        }
    
    def initialize_provider(self, instance, created):
        self.aws_credentials(instance.config)
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
