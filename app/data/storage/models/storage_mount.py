from systems import models
from systems.models import environment, subnet, provider
from data.network import models as network
from data.storage import models as storage


class StorageMountFacade(
    provider.ProviderModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    def set_storage_scope(self, storage):
        super().set_scope(storage_id = storage.id)
    
    def set_network_scope(self, network):
        super().set_scope(subnet__network__id = network.id)

    def set_subnet_scope(self, subnet):
        super().set_scope(subnet_id = subnet.id)


class StorageMount(
    provider.ProviderMixin,
    subnet.SubnetMixin,
    environment.EnvironmentModel  
):    
    remote_host = models.CharField(null=True, max_length=128)
    remote_path = models.CharField(null=True, max_length=256)
    mount_options = models.TextField(null=True)
 
    storage = models.ForeignKey(storage.Storage, on_delete=models.PROTECT)
    firewalls = models.ManyToManyField(network.Firewall)

    class Meta:
        facade_class = StorageMountFacade

    def __str__(self):
        return "{} ({}:{})".format(self.name, self.remote_host, self.remote_path)

    def get_provider_name(self):
        return 'storage:mount'
