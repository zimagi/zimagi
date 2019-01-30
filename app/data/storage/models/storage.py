
from systems import models
from data.environment import models as env
from data.network import models as network


class StorageFacade(models.ConfigModelFacade):

    def get_packages(self):
        return super().get_packages() + ['storage']


    def key(self):
        return 'name'
 
    def scope(self, fields = False):
        if fields:
            return ('environment',)
        
        curr_env = env.Environment.facade.get_env()
        if not curr_env:
            return False

        return { 'environment_id': curr_env }

    def set_scope(self, network):
        super().set_scope(network_id = network.id)


class Storage(models.AppConfigModel):
    name = models.CharField(max_length=128)
    type = models.CharField(null=True, max_length=128)

    network = models.ForeignKey(network.Network, related_name='storage', null=True, on_delete=models.PROTECT)
    environment = models.ForeignKey(env.Environment, related_name='storage', on_delete=models.PROTECT)

    class Meta:
        unique_together = ('environment', 'name')
        facade_class = StorageFacade

    def __str__(self):
        return "{} ({})".format(self.name, self.type)


    def initialize(self, command):
        self.provider = command.get_provider('storage', self.type, storage = self)
        return True
