from data.network.models import Network
from data.subnet.models import Subnet
from data.firewall.models import Firewall
from data.firewall_rule.models import FirewallRule
from . import DataMixin


class NetworkMixin(DataMixin):

    schema = {
        'network': {
            'facade': Network,
            'provider': True,
            'system_fields': (
                'environment',
                'type',
                'config',
                'variables',
                'state_config',
                'created', 
                'updated'
            )
        },
        'subnet': {
            'facade': Subnet,
            'system_fields': (
                'network',
                'type',
                'config',
                'variables',
                'state_config',
                'created', 
                'updated'
            )
        },
        'firewall': {
            'facade': Firewall,
            'system_fields': (
                'network',
                'type',
                'config',
                'variables',
                'state_config',
                'created', 
                'updated'
            )
        },
        'firewall_rule': {
            'facade': FirewallRule,
            'system_fields': (
                'firewall',
                'type',
                'config',
                'variables',
                'state_config',
                'created', 
                'updated'
            )
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['01_network'] = self._network
        self.facade_index['02_subnet'] = self._subnet
        self.facade_index['02_firewall'] = self._firewall
        self.facade_index['03_firewall_rule'] = self._firewall_rule


    def set_subnet_scope(self):
        if self.subnet_name and ':' in self.subnet_name:
            components = self.subnet_name.split(':')
            self.options.add('network_name', components[0].strip())
            self.options.add('subnet_name', components[1].strip())

        if self.network_name:
            self._subnet.set_scope(self.network)


    def set_firewall_scope(self):
        if self.firewall_name and ':' in self.firewall_name:
            components = self.firewall_name.split(':')
            self.options.add('network_name', components[0].strip())
            self.options.add('firewall_name', components[1].strip())

        if self.network_name:
            self._firewall.set_scope(self.network)


    def set_firewall_rule_scope(self):
        if self.firewall_rule_name and ':' in self.firewall_rule_name:
            components = self.firewall_rule_name.split(':')
            component_count = len(components)

            if component_count == 3:
                self.options.add('network_name', components[0].strip())
                self.options.add('firewall_name', components[1].strip())
                self.options.add('firewall_rule_name', components[2].strip())
            elif component_count == 2:
                self.options.add('firewall_name', components[0].strip())
                self.options.add('firewall_rule_name', components[1].strip())
            else:
                self.error("Wrong number of firewall sections; need 'network:firewall:rule' or 'firewall:rule' with '@network' defined".format())

        self._firewall.set_scope(self.network)
        self._firewall_rule.set_scope(self.firewall)
