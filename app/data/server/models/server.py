from settings import Roles
from systems import models
from systems.models import environment, subnet, provider
from data.network import models as network
from data.server import models as server


class ServerFacade(
    provider.ProviderModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    def set_network_scope(self, network):
        super().set_scope(subnet__network__id = network.id)

    def set_subnet_scope(self, subnet):
        super().set_scope(subnet_id = subnet.id)


class Server(
    provider.ProviderMixin,
    subnet.SubnetMixin,
    environment.EnvironmentModel
):
    public_ip = models.CharField(null=True, max_length=128)
    private_ip = models.CharField(null=True, max_length=128)
    user = models.CharField(null=True, max_length=128)
    password = models.EncryptedCharField(null=True, max_length=1096)
    private_key = models.EncryptedTextField(null=True)
    data_device = models.CharField(null=True, max_length=256)
    backup_device = models.CharField(null=True, max_length=256)
 
    firewalls = models.ManyToManyField(network.Firewall)
    groups = models.ManyToManyField(server.ServerGroup)

    class Meta:
        facade_class = ServerFacade

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.STATUS_RUNNING = 'running'
        self.STATUS_UNREACHABLE = 'unreachable'

    def __str__(self):
        return "{} ({})".format(self.name, self.ip)


    def initialize(self, command):
        if not super().initialize(command):
            return False
        
        groups = [
            Roles.admin, 
            Roles.server_admin
        ] + list(self.groups.all().values_list('name', flat = True))
        
        if not command.check_access(groups):
            return False
        
        self.status = self.STATUS_RUNNING if self.ping() else self.STATUS_UNREACHABLE
        return True
    
    def get_provider_name(self):
        return 'compute'


    def running(self):
        if self.status == self.STATUS_RUNNING:
            return True
        return False

    def ping(self, port = 22):
        return self.provider.ping(port = port)
