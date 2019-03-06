from django.db import models as django

from systems.models import group, network, provider


class StorageFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    network.NetworkModelFacadeMixin
):
    def get_provider_name(self):
        return 'storage:storage'
    
    def get_children(self):
        return (
            'mount',
        )
    
    def get_scopes(self):
        return (
            'network',
        )
    
    def get_relations(self):
        return {
            'groups': ('group', 'Groups', '--groups'),
            'storagemount_relation': ('mount', 'Mounts')
        }

    def default_order(self):
        return 'name'

    def get_list_fields(self):
        return (
            ('name', 'Name'),
            ('network', 'Network'),
            ('type', 'Type'),
            ('config', 'Configuration')
        )
    
    def get_display_fields(self):
        return (
            ('name', 'Name'),
            ('network', 'Network'),
            ('type', 'Type'),
            '---',
            ('config', 'Configuration'),
            '---',
            ('variables', 'Variables'),
            ('state_config', 'State'),
            '---',
            ('created', 'Created'),
            ('updated', 'Updated')
        )


class Storage(
    provider.ProviderMixin,
    group.GroupMixin,
    network.NetworkModel
):
    class Meta(network.NetworkModel.Meta):
        facade_class = StorageFacade

    def __str__(self):
        return "{}".format(self.name)
