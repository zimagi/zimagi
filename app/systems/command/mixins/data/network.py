from django.core.management.base import CommandError

from . import DataMixin
from data.network.models import Network
from data.subnet.models import Subnet
from data.firewall.models import Firewall
from data.firewall_rule.models import FirewallRule
from utility import config


class NetworkMixin(DataMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['01_network'] = self._network
        self.facade_index['02_subnet'] = self._subnet
        self.facade_index['02_firewall'] = self._firewall
        self.facade_index['03_firewall_rule'] = self._firewall_rule


    def parse_network_provider_name(self, optional = False, help_text = 'network resource provider (default @network_provider|internal)'):
        self.parse_variable('network_provider_name', optional, str, help_text, 
            value_label = 'NAME'
        )

    @property
    def network_provider_name(self):
        name = self.options.get('network_provider_name', None)
        if not name:
            name = self.get_config('network_provider', required = False)
        if not name:
            name = config.Config.string('NETWORK_PROVIDER', 'internal')
        return name

    @property
    def network_provider(self):
        return self.get_provider('network', self.network_provider_name)


    def parse_network_name(self, optional = False, help_text = 'unique environment network name (defaults to @network)'):
        self.parse_variable('network_name', optional, str, help_text, 
            value_label = 'NAME'
        )

    @property
    def network_name(self):
        name = self.options.get('network_name', None)
        if not name:
            name = self.get_config('network', required = False)
        return name

    @property
    def network(self):
        return self.get_instance(self._network, self.network_name)
    
    def parse_network_names(self, flag = '--networks', help_text = 'one or more network names'):
        self.parse_variables('network_names', flag, str, help_text, 
            value_label = 'NAME'
        )

    @property
    def network_names(self):
        return self.options.get('network_names', [])


    def parse_network_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._network, 'network_fields', 
            optional = optional, 
            excluded_fields = (
                'created', 
                'updated', 
                'environment',
                'type',
                'config',
                'variables',
                'state_config'
            ),
            help_callback = help_callback,
            callback_args = ['network']
        )

    @property
    def network_fields(self):
        return self.options.get('network_fields', {})


    def parse_network_order(self, optional = '--order', help_text = 'network ordering fields (~field for desc)'):
        self.parse_variables('network_order', optional, str, help_text, 
            value_label = '[~]FIELD'
        )

    @property
    def network_order(self):
        return self.options.get('network_order', [])


    def parse_network_search(self, optional = True, help_text = 'network search fields'):
        self.parse_variables('network_search', optional, str, help_text, 
            value_label = 'REFERENCE'
        )

    @property
    def network_search(self):
        return self.options.get('network_search', [])

    @property
    def network_instances(self):
        return self.search_instances(self._network, self.network_search)


    def parse_subnet_name(self, optional = False, help_text = 'unique network subnet name'):
        self.parse_variable('subnet_name', optional, str, help_text, 
            value_label = 'NAME'
        )

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
        self.parse_variables('subnet_names', flag, str, help_text, 
            value_label = 'NAME'
        )

    @property
    def subnet_names(self):
        return self.options.get('subnet_names', [])


    def parse_subnet_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._subnet, 'subnet_fields', 
            optional = optional, 
            excluded_fields = (
                'created', 
                'updated', 
                'network',
                'config'
            ),
            help_callback = help_callback,
            callback_args = ['subnet']
        )

    @property
    def subnet_fields(self):
        return self.options.get('subnet_fields', {})


    def parse_firewall_name(self, optional = False, help_text = 'unique network firewall name'):
        self.parse_variable('firewall_name', optional, str, help_text, 
            value_label = 'NAME'
        )

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
        self.parse_variables('firewall_names', flag, str, help_text, 
            value_label = 'NAME'
        )

    @property
    def firewall_names(self):
        return self.options.get('firewall_names', [])


    def parse_firewall_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._firewall, 'firewall_fields', 
            optional = optional, 
            excluded_fields = (
                'created', 
                'updated', 
                'network',
                'config'
            ),
            help_callback = help_callback,
            callback_args = ['firewall']
        )

    @property
    def firewall_fields(self):
        return self.options.get('firewall_fields', {})


    def parse_firewall_rule_name(self, optional = False, help_text = 'unique network firewall rule name'):
        self.parse_variable('firewall_rule_name', optional, str, help_text, 
            value_label = 'NAME'
        )

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


    def parse_firewall_rule_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._firewall, 'firewall_rule_fields', 
            optional = optional, 
            excluded_fields = (
                'created', 
                'updated', 
                'firewall',
                'config'
            ),
            help_callback = help_callback,
            callback_args = ['firewall_rule']
        )

    @property
    def firewall_rule_fields(self):
        return self.options.get('firewall_rule_fields', {})


    @property
    def _network(self):
        return self.facade(Network.facade)

    @property
    def _subnet(self):
        return self.facade(Subnet.facade)

    @property
    def _firewall(self):
        return self.facade(Firewall.facade)

    @property
    def _firewall_rule(self):
        return self.facade(FirewallRule.facade)
