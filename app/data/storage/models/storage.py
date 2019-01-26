
from systems import models
from data.environment import models as env

import json


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


class Storage(models.AppConfigModel):
    name = models.CharField(max_length=128)
    type = models.CharField(null=True, max_length=128)
    fs_name = models.CharField(null=True, max_length=128)
    region = models.CharField(null=True, max_length=128)
    zone = models.CharField(null=True, max_length=128)       
    
    remote_host = models.CharField(null=True, max_length=128)
    remote_path = models.CharField(null=True, max_length=256)
    mount_options = models.TextField(null=True)
 
    environment = models.ForeignKey(env.Environment, related_name='filesystems', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('environment', 'name')
        facade_class = StorageFacade

    def __str__(self):
        return "{} ({}:{})".format(self.name, self.type, self.name)


    def initialize(self, command):
        self.provider = command.get_provider('storage', self.type, storage = self)
        self.state = None
        return True
