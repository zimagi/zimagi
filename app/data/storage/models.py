from django.db import models as django

from systems.models import group, network, provider


class StorageFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    network.NetworkModelFacadeMixin
):
    def get_provider_name(self):
        return 'storage:storage'
    
    def get_relations(self):
        return {
            'groups': ('group', 'group_names', '--groups')
        }


class Storage(
    provider.ProviderMixin,
    group.GroupMixin,
    network.NetworkModel
):
    class Meta(network.NetworkModel.Meta):
        facade_class = StorageFacade

    def __str__(self):
        return "{}".format(self.name)
