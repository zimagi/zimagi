from systems import models
from data.network import models as network
from data.storage import models as storage


class StorageMountFacade(models.ConfigModelFacade):

    def get_packages(self):
        return super().get_packages() + ['storage']

    def key(self):
        return 'name'

    def set_scope(self, storage):
        super().set_scope(storage_id = storage.id)


class StorageMount(models.AppConfigModel):
    
    name = models.CharField(max_length=128)
    remote_host = models.CharField(null=True, max_length=128)
    remote_path = models.CharField(null=True, max_length=256)
    mount_options = models.TextField(null=True)
 
    storage = models.ForeignKey(storage.Storage, related_name='mounts', on_delete=models.PROTECT)
    subnet = models.ForeignKey(network.Subnet, related_name='mounts', null=True, on_delete=models.PROTECT)
    firewalls = models.ManyToManyField(network.Firewall, related_name='mounts')

    class Meta:
        unique_together = ('storage', 'name')
        facade_class = StorageMountFacade

    def __str__(self):
        return "{} ({}:{})".format(self.name, self.remote_host, self.remote_path)
