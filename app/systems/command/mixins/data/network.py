from data.network.models import Network
from data.subnet.models import Subnet
from data.firewall.models import Firewall
from data.firewall_rule.models import FirewallRule
from . import DataMixin


class NetworkMixin(DataMixin):

    schema = {
        'network': {
            'model': Network,
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
            'model': Subnet,
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
            'model': Firewall,
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
            'model': FirewallRule,
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
