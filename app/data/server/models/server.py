from settings import Roles
from systems import models
from data.environment import models as env
from data.server import models as server

import json


class ServerFacade(models.ModelFacade):

    def __init__(self, cls):
        super().__init__(cls)

        self.fields.append('config')


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


    def render(self, fields, queryset_values):
        data = super().render(fields, queryset_values)
        
        pw_index = data[0].index('password')
        priv_key_index = data[0].index('private_key')

        for index in range(1, len(data)):
            record = data[index]
            
            if record[pw_index]:
                record[pw_index] = '*****'
            
            if record[priv_key_index]:
                record[priv_key_index] = '*****'

        return data


class Server(models.AppModel):

    name = models.CharField(max_length=128)
    ip = models.CharField(null=True, max_length=128)
    type = models.CharField(null=True, max_length=128)
    _config = models.TextField(db_column="config", null=True)
       
    user = models.CharField(null=True, max_length=128)
    password = models.CharField(null=True, max_length=256)
    private_key = models.TextField(null=True)

    region = models.CharField(null=True, max_length=128)
    zone = models.CharField(null=True, max_length=128)
    data_device = models.CharField(null=True, max_length=256)
    backup_device = models.CharField(null=True, max_length=256)
 
    environment = models.ForeignKey(env.Environment, related_name='servers', on_delete=models.CASCADE)
    groups = models.ManyToManyField(server.ServerGroup, related_name='servers', blank=True)

    @property
    def config(self):
        if self._config:        
            return json.loads(self._config)
        return {}

    @config.setter
    def config(self, data):
        if not isinstance(data, str):
            data = json.dumps(data)
        
        self._config = data

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
            Roles.server_admin, 
            Roles.server_group_admin
        ] + list(self.groups.all().values_list('name', flat = True))
        
        if not command.check_access(groups):
            return False
        
        self.provider = command.get_provider('compute', self.type, server = self)
        self.state = self.STATE_RUNNING if self.ping() else self.STATE_UNREACHABLE
        return True


    def running(self, server):
        if self.state == self.STATE_RUNNING:
            return True
        return False

    def ping(self, port = 22):
        return self.provider.ping(port = port)
