from django.db import models as django

from systems.models import environment, group, provider


class NetworkFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    def get_provider_name(self):
        return 'network:network'

    def get_children(self):
        return (
            'subnet',
            'firewall',
            'storage'
        )

    def get_relations(self):
        return {
            'groups': ('group', 'Groups', '--groups'),
            'subnet_relation': ('subnet', 'Subnets'),
            'firewall_relation': ('firewall', 'Firewalls'),
            'storage_relation': ('storage', 'Storage')
        }

    def default_order(self):
        return 'cidr'

    def get_list_fields(self):
        return (
            ('name', 'Name'),
            ('type', 'Type'),
            ('cidr', 'CIDR'),
            ('config', 'Configuration'),
            ('variables', 'Resources')
        )

    def get_display_fields(self):
        return (
            ('name', 'Name'),
            ('environment', 'Environment'),
            ('type', 'Type'),
            ('cidr', 'CIDR'),
            '---',
            ('config', 'Configuration'),
            '---',
            ('variables', 'Resources'),
            ('state_config', 'State'),
            '---',
            ('created', 'Created'),
            ('updated', 'Updated')
        )

    def get_field_cidr_display(self, instance, value, short):
        return value


class Network(
    provider.ProviderMixin,
    group.GroupMixin,
    environment.EnvironmentModel
):
    cidr = django.CharField(null=True, max_length=128)

    class Meta(environment.EnvironmentModel.Meta):
        facade_class = NetworkFacade
