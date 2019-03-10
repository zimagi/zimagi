from utility.cloud import AWSServiceMixin
from .base import *


class AWSNetworkProvider(AWSServiceMixin, NetworkProvider):

    def provider_config(self, type = None):
        super().provider_config(type)
        self.option(str, 'region', 'us-east-1', help = 'AWS region name', config_name = 'aws_region')
        self.option(str, 'tenancy', 'default', help = 'AWS VPC instance tenancy (default | dedicated)', config_name = 'aws_vpc_tenancy')
        self.option(bool, 'dns_support', True, help = 'AWS VPC DNS support', config_name = 'aws_vpc_dns_support')
        self.option(bool, 'dns_hostnames', False, help = 'AWS VPC DNS hostname assignment', config_name = 'aws_vpc_dns_hostnames')

    def initialize_terraform(self, instance, created):
        self.aws_credentials(instance.config)
        super().initialize_terraform(instance, created)

    def finalize_terraform(self, instance):
        self.aws_credentials(instance.config)
        super().finalize_terraform(instance)

    def prepare_instance(self, instance, created):
        super().prepare_instance(instance, created)
        self.clean_aws_credentials(instance.config)


class AWSSubnetProvider(AWSServiceMixin, SubnetProvider):

    def provider_config(self, type = None):
        super().provider_config(type)
        self.option(str, 'zone', None, help = 'AWS availability zone (default random)', config_name = 'aws_zone')
        self.option(str, 'zone_suffix', None, help = 'AWS availability zone suffix (appended to region)', config_name = 'aws_zone_suffix')
        self.option(bool, 'use_public_ip', True, help = 'Enable public IP addresses for instances in subnet', config_name = 'aws_public_ip')

    def initialize_terraform(self, instance, created):
        self.aws_credentials(instance.config)

        if instance.config['zone'] is None and instance.config['zone_suffix'] is not None:
            instance.config['zone'] = "{}{}".format(
                instance.network.config['region'],
                instance.config['zone_suffix']
            )
        super().initialize_terraform(instance, created)

    def finalize_terraform(self, instance):
        self.aws_credentials(instance.config)
        super().finalize_terraform(instance)

    def prepare_instance(self, instance, created):
        super().prepare_instance(instance, created)
        self.clean_aws_credentials(instance.config)


class AWSFirewallProvider(AWSServiceMixin, FirewallProvider):

    def initialize_terraform(self, instance, created):
        self.aws_credentials(instance.config)
        super().initialize_terraform(instance, created)

    def finalize_terraform(self, instance):
        self.aws_credentials(instance.config)
        super().finalize_terraform(instance)

    def prepare_instance(self, instance, created):
        super().prepare_instance(instance, created)
        self.clean_aws_credentials(instance.config)


class AWSFirewallRuleProvider(AWSServiceMixin, FirewallRuleProvider):

    def initialize_terraform(self, instance, created):
        self.aws_credentials(instance.config)
        super().initialize_terraform(instance, created)

    def finalize_terraform(self, instance):
        self.aws_credentials(instance.config)
        super().finalize_terraform(instance)

    def prepare_instance(self, instance, created):
        super().prepare_instance(instance, created)
        self.clean_aws_credentials(instance.config)


class AWS(BaseNetworkProvider):

    def register_types(self):
        super().register_types()
        self.set('network', AWSNetworkProvider)
        self.set('subnet', AWSSubnetProvider)
        self.set('firewall', AWSFirewallProvider)
        self.set('firewall_rule', AWSFirewallRuleProvider)
