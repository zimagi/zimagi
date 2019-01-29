from settings import Roles
from systems import models
from data.environment import models as env
from data.network import models as network
from data.server import models as server

import json


class ServerFacade(models.ConfigModelFacade):

    def get_packages(self):
        return super().get_packages() + ['server']


    def key(self):
        return 'name'
 
    def scope(self, fields = False):
        if fields:
            return ('environment',)
        
        curr_env = env.Environment.facade.get_env()
        if not curr_env:
            return False

        return { 'environment_id': curr_env }

    def set_network_scope(self, network):
        super().set_scope(subnet__network__id = network.id)

    def set_subnet_scope(self, subnet):
        super().set_scope(subnet__id = subnet.id)


class Server(models.AppConfigModel):

    name = models.CharField(max_length=128)
    ip = models.CharField(null=True, max_length=128)
    type = models.CharField(null=True, max_length=128)
       
    user = models.CharField(null=True, max_length=128)
    password = models.CharField(null=True, max_length=256)
    private_key = models.TextField(null=True)

    data_device = models.CharField(null=True, max_length=256)
    backup_device = models.CharField(null=True, max_length=256)
 
    subnet = models.ForeignKey(network.Subnet, related_name='servers', null=True, on_delete=models.PROTECT)
    firewalls = models.ManyToManyField(network.Firewall, related_name='servers')
    environment = models.ForeignKey(env.Environment, related_name='servers', on_delete=models.PROTECT)
    groups = models.ManyToManyField(server.ServerGroup, related_name='servers')

    class Meta:
        unique_together = ('environment', 'name')
        facade_class = ServerFacade


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.STATE_RUNNING = 'running'
        self.STATE_UNREACHABLE = 'unreachable'


    def __str__(self):
        return "{} ({})".format(self.name, self.ip)


    def initialize(self, command):
        groups = [
            Roles.admin, 
            Roles.server_admin
        ] + list(self.groups.all().values_list('name', flat = True))
        
        if not command.check_access(groups):
            return False
        
        self.provider = command.get_provider('compute', self.type, server = self)
        self.state = self.STATE_RUNNING if self.ping() else self.STATE_UNREACHABLE
        return True


    def add_groups(self, groups):
        groups = [groups] if isinstance(groups, str) else groups
        for group in groups:
            group, created = server.ServerGroup.objects.get_or_create(name = group)
            self.groups.add(group)

    def remove_groups(self, groups):
        groups = [groups] if isinstance(groups, str) else groups
        self.groups.filter(name__in = groups).delete()


    def running(self, server):
        if self.state == self.STATE_RUNNING:
            return True
        return False

    def ping(self, port = 22):
        return self.provider.ping(port = port)
