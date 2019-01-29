from django.core.management.base import CommandError

from . import DataMixin
from data.network import models


class NetworkMixin(DataMixin):

    def parse_network_provider_name(self, optional = False, help_text = 'network resource provider'):
        self.parse_variable('network_provider_name', optional, str, help_text, 'NAME')

    @property
    def network_provider_name(self):
        return self.options.get('network_provider_name', None)

    @property
    def network_provider(self):
        return self.get_provider('network', self.network_provider_name)

    def parse_network_name(self, optional = False, help_text = 'unique environment network name (defaults to @network)'):
        self.parse_variable('network_name', optional, str, help_text, 'NAME')

    @property
    def network_name(self):
        name = self.options.get('network_name', None)
        if not name:
            name = self.get_config('network', required = False)
        return name

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
        self.parse_variable('subnet_name', optional, str, help_text, 'NAME')

    @property
    def subnet_name(self):
        return self.options.get('subnet_name', None)

    def set_subnet_scope(self):
        if self.subnet_name and ':' in self.subnet_name:
            components = self.subnet_name.split(':')
            self.options.add('network_name', components[0].strip())
            self.options.add('subnet_name', components[1].strip())

        if self.network_name:
            self._subnet.set_scope(self.network)

    @property
    def subnet(self):
        return self.get_instance(self._subnet, self.subnet_name)
    
    def parse_subnet_names(self, flag = '--subnets', help_text = 'one or more network subnet names'):
        self.parse_variables('subnet_names', flag, str, help_text, 'NAME')

    @property
    def subnet_names(self):
        return self.options.get('subnet_names', [])

    @property
    def subnets(self):
        if self.subnet_names:
            return self.get_instances(self._subnet, 
                names = self.subnet_names
            )
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
        self.parse_variable('firewall_name', optional, str, help_text, 'NAME')

    @property
    def firewall_name(self):
        return self.options.get('firewall_name', None)

    def set_firewall_scope(self):
        if self.firewall_name and ':' in self.firewall_name:
            components = self.firewall_name.split(':')
            self.options.add('network_name', components[0].strip())
            self.options.add('firewall_name', components[1].strip())

        if self.network_name:
            self._firewall.set_scope(self.network)

    @property
    def firewall(self):
        return self.get_instance(self._firewall, self.firewall_name)

    
    def parse_firewall_names(self, flag = '--firewalls', help_text = 'one or more network firewall names'):
        self.parse_variables('firewall_names', flag, str, help_text, 'NAME')

    @property
    def firewall_names(self):
        return self.options.get('firewall_names', [])

    @property
    def firewalls(self):
        if self.firewall_names:
            return self.get_instances(self._firewall, 
                names = self.firewall_names
            )
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
        self.parse_variable('firewall_rule_name', optional, str, help_text, 'NAME')

    @property
    def firewall_rule_name(self):
        return self.options.get('firewall_rule_name', None)

    def set_firewall_rule_scope(self):
        if self.firewall_rule_name and ':' in self.firewall_rule_name:
            components = self.firewall_rule_name.split(':')
            component_count = len(components)

            if component_count == 3:
                self.options.add('network_name', components[0].strip())
                self.options.add('firewall_name', components[1].strip())
                self.optionsadd('firewall_rule_name', components[2].strip())
            elif component_count == 2:
                self.options.add('firewall_name', components[0].strip())
                self.options.add('firewall_rule_name', components[1].strip())
            else:
                self.error("Wrong number of firewall sections; need 'network:firewall:rule' or 'firewall:rule' with '@network' defined".format())

        self._firewall.set_scope(self.network)
        self._firewall_rule.set_scope(self.firewall)

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
        return self.facade(models.Network.facade)

    @property
    def _subnet(self):
        return self.facade(models.Subnet.facade)

    @property
    def _firewall(self):
        return self.facade(models.Firewall.facade)

    @property
    def _firewall_rule(self):
        return self.facade(models.FirewallRule.facade)
