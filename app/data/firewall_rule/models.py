from django.db import models as django

from systems.models import fields, firewall, provider


class FirewallRuleFacade(
    provider.ProviderModelFacadeMixin,
    firewall.FirewallModelFacadeMixin
):
    def get_provider_name(self):
        return 'network:firewall_rule'
    
    def get_provider_relation(self):
        return 'firewall'
    
    def get_scopes(self):
        return {
            'firewall': ('network', 'network_name', '--network'),
            'firewall_rule': ('firewall', 'firewall_name', '--firewall')
        }

    def default_order(self):
        return 'name'

    def get_list_fields(self):
        return (
            ('name', 'Name'),
            ('firewall__network', 'Network'),
            ('firewall', 'Firewall'),
            ('type', 'Type'),
            ('mode', 'Mode'),
            ('protocol', 'Protocol'),
            ('from_port', 'From port'),
            ('to_port', 'To port'),
            ('cidrs', 'CIDRs')
        )
    
    def get_display_fields(self):
        return (
            ('name', 'Name'),
            ('firewall__network', 'Network'),
            ('firewall', 'Firewall'),
            ('type', 'Type'),
            '---',
            ('config', 'Configuration'),
            '---',
            ('mode', 'Mode'),
            ('protocol', 'Protocol'),
            ('from_port', 'From port'),
            ('to_port', 'To port'),
            ('cidrs', 'CIDRs'),
            '---',
            ('variables', 'Variables'),
            ('state_config', 'State'),
            '---',
            ('created', 'Created'),
            ('updated', 'Updated')
        )


class FirewallRule(
    provider.ProviderMixin,
    firewall.FirewallModel
):
    mode = django.CharField(max_length=10, default='ingress', choices=[(i, i) for i in ('ingress', 'egress')])
    from_port = django.IntegerField(null=True)
    to_port = django.IntegerField(null=True)
    protocol = django.CharField(max_length=10, default='tcp', choices=[(i, i) for i in ('tcp', 'udp', 'icmp')])
    cidrs = fields.CSVField(null=True)

    class Meta(firewall.FirewallModel.Meta):
        facade_class = FirewallRuleFacade

    def __str__(self):
        return "{}".format(self.name)
