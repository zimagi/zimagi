from django.db import models as django

from systems.models import group, network, provider


class FirewallFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    network.NetworkModelFacadeMixin
):
    def get_provider_name(self):
        return 'network:firewall'

    def get_provider_relation(self):
        return 'network'

    def get_children(self):
        return (
            'firewall_rule',
        )

    def get_scopes(self):
        return (
            'network',
        )

    def get_relations(self):
        return {
            'groups': ('group', 'Groups', '--groups'),
            'firewallrule_relation': ('firewall_rule', 'Rules')
        }

    def default_order(self):
        return 'name'

    def get_list_fields(self):
        return (
            ('name', 'Name'),
            ('network', 'Network'),
            ('type', 'Type'),
            ('config', 'Configuration'),
            ('variables', 'Resources')
        )

    def get_display_fields(self):
        return (
            ('name', 'Name'),
            ('network', 'Network'),
            ('type', 'Type'),
            '---',
            ('config', 'Configuration'),
            '---',
            ('variables', 'Resources'),
            ('state_config', 'State'),
            '---',
            ('created', 'Created'),
            ('updated', 'Updated')
        )


class Firewall(
    provider.ProviderMixin,
    group.GroupMixin,
    network.NetworkModel
):
    class Meta(network.NetworkModel.Meta):
        facade_class = FirewallFacade

    def __str__(self):
        return "{}".format(self.name)
