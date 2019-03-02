from django.db import models as django

from systems.models import network, group, provider


class SubnetFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    network.NetworkModelFacadeMixin
):
    def get_provider_name(self):
        return 'network:subnet'
    
    def get_scopes(self):
        return {
            'network': ('network', 'network_name', '--network')
        }
    
    def get_relations(self):
        return {
            'groups': ('group', 'group_names', '--groups'),
            #'mounts': ('mount', 'mount_names'), 
            #'servers': ('server', 'server_names')
        }

    def default_order(self):
        return 'cidr'

    def get_list_fields(self):
        return (
            ('name', 'Name'),
            ('network', 'Network'),
            ('type', 'Type'),            
            ('cidr', 'CIDR')
        )
    
    def get_display_fields(self):
        return (
            ('name', 'Name'),
            ('network', 'Network'),
            ('type', 'Type'),
            ('cidr', 'CIDR'),
            '---',
            ('config', 'Configuration'),
            '---',
            ('variables', 'Variables'),
            ('state_config', 'State'),
            '---',
            ('created', 'Created'),
            ('updated', 'Updated')
        )
    
    def get_field_cidr_display(self, instance, value, short):
        return value


class Subnet(
    provider.ProviderMixin,
    group.GroupMixin,
    network.NetworkModel
):
    cidr = django.CharField(null=True, max_length=128)

    class Meta(network.NetworkModel.Meta):
        facade_class = SubnetFacade

    def __str__(self):
        return "{} ({})".format(self.name, self.cidr)
