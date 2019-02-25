from django.db import models as django

from systems.models import environment, subnet, storage, firewall, provider


class StorageMountFacade(
    provider.ProviderModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    def get_provider_name(self):
        return 'storage:mount'

    def set_storage_scope(self, storage):
        super().set_scope(storage_id = storage.id)
    
    def set_network_scope(self, network):
        super().set_scope(subnet__network__id = network.id)

    def set_subnet_scope(self, subnet):
        super().set_scope(subnet_id = subnet.id)


class StorageMount(
    provider.ProviderMixin,
    subnet.SubnetMixin,
    storage.StorageMixin,
    firewall.FirewallRelationMixin,
    environment.EnvironmentModel  
):    
    remote_host = django.CharField(null=True, max_length=128)
    remote_path = django.CharField(null=True, max_length=256)
    mount_options = django.TextField(null=True)
    
    class Meta(environment.EnvironmentModel.Meta):
        facade_class = StorageMountFacade

    def __str__(self):
        return "{} ({}:{})".format(self.name, self.remote_host, self.remote_path)
