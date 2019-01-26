from django.core.management.base import CommandError

from . import DataMixin
from data.network import models


class NetworkMixin(DataMixin):

    def parse_network_provider_name(self, optional = False, help_text = 'network resource provider'):
        self.parse_variable('network_provider_name', optional, str, help_text)

    @property
    def network_provider_name(self):
        return self.options.get('network_provider_name', None)

    @property
    def network_provider(self):
        return self.get_provider('network', self.network_provider_name)

    def parse_network_name(self, optional = False, help_text = 'unique environment network name'):
        self.parse_variable('network_name', optional, str, help_text)

    @property
    def network_name(self):
        return self.options.get('network_name', None)

    @property
    def network(self):
        return self.get_instance(self._network, self.network_name)

    @property
    def networks(self):
        return self.get_instances(self._network)

    def parse_network_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._network, 'network_fields', optional, 
            (
                'created', 
                'updated', 
                'environment',
                'config'
            ),
            help_callback,
            callback_args = ['network']
        )

    @property
    def network_fields(self):
        return self.options.get('network_fields', {})


    def parse_subnet_name(self, optional = False, help_text = 'unique network subnet name'):
        self.parse_variable('subnet_name', optional, str, help_text)

    @property
    def subnet_name(self):
        return self.options.get('subnet_name', None)

    @property
    def subnet(self):
        return self.get_instance(self._subnet, self.subnet_name)

    @property
    def subnets(self):
        return self.get_instances(self._subnet)

    def parse_subnet_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._subnet, 'subnet_fields', optional, 
            (
                'created', 
                'updated', 
                'network',
                'config'
            ),
            help_callback,
            callback_args = ['subnet']
        )

    @property
    def subnet_fields(self):
        return self.options.get('subnet_fields', {})


    def parse_firewall_name(self, optional = False, help_text = 'unique network firewall name'):
        self.parse_variable('firewall_name', optional, str, help_text)

    @property
    def firewall_name(self):
        return self.options.get('firewall_name', None)

    @property
    def firewall(self):
        return self.get_instance(self._firewall, self.firewall_name)

    @property
    def firewalls(self):
        return self.get_instances(self._firewall)

    def parse_firewall_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._firewall, 'firewall_fields', optional, 
            (
                'created', 
                'updated', 
                'network',
                'config'
            ),
            help_callback,
            callback_args = ['firewall']
        )

    @property
    def firewall_fields(self):
        return self.options.get('firewall_fields', {})


    def parse_firewall_rule_name(self, optional = False, help_text = 'unique network firewall rule name'):
        self.parse_variable('firewall_rule_name', optional, str, help_text)

    @property
    def firewall_rule_name(self):
        return self.options.get('firewall_rule_name', None)

    @property
    def firewall_rule(self):
        return self.get_instance(self._firewall_rule, self.firewall_rule_name)

    @property
    def firewall_rules(self):
        return self.get_instances(self._firewall_rule)

    def parse_firewall_rule_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._firewall, 'firewall_rule_fields', optional, 
            (
                'created', 
                'updated', 
                'firewall',
                'config'
            ),
            help_callback,
            callback_args = ['firewall_rule']
        )

    @property
    def firewall_rule_fields(self):
        return self.options.get('firewall_rule_fields', {})


    @property
    def _network(self):
        return models.Network.facade

    @property
    def _subnet(self):
        return models.Subnet.facade

    @property
    def _firewall(self):
        return models.Firewall.facade

    @property
    def _firewall_rule(self):
        return models.FirewallRule.facade
