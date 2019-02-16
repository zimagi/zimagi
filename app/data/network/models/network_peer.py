from systems import models
from data.environment import models as env
from data.network import models as network


class NetworkPeerFacade(models.ProviderModelFacade):

    def get_packages(self):
        return super().get_packages() + ['network', 'server']

    def key(self):
        return 'name'
 
    def scope(self, fields = False):
        if fields:
            return ('environment',)
        
        curr_env = env.Environment.facade.get_env()
        if not curr_env:
            return False

        return { 'environment_id': curr_env }


class NetworkPeer(models.AppProviderModel):

    name = models.CharField(max_length=128)
    type = models.CharField(null=True, max_length=128)
    
    peers = models.ManyToManyField(network.Network)    
    environment = models.ForeignKey(env.Environment, related_name='network_peers', on_delete=models.PROTECT)

    class Meta:
        unique_together = ('environment', 'name')
        facade_class = NetworkPeerFacade

    def __str__(self):
        return self.name

    def initialize(self, command):
        self.provider = command.get_provider('network:network_peer', self.type, instance = self)
        return True
