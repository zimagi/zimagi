from django.conf import settings

from systems import models
from data.environment import models as env

import json


class ProjectFacade(models.ModelFacade):

    def __init__(self, cls):
        super().__init__(cls)

        self.fields.append('config')


    def get_packages(self):
        return super().get_packages() + ['project']


    def ensure(self, env, user):
        project = self.retrieve(settings.CORE_PROJECT)

        if not project:
            self.store(settings.CORE_PROJECT, 
                type = 'internal'
            )


    def key(self):
        return 'name'
 
    def scope(self, fields = False):
        if fields:
            return ('environment',)
        
        curr_env = env.Environment.facade.get_env()
        if not curr_env:
            return False

        return { 'environment_id': curr_env }


class Project(models.AppModel):
    name = models.CharField(max_length=128)
    type = models.CharField(null=True, max_length=128)
    _config = models.TextField(db_column="config", null=True)
       
    remote = models.CharField(null=True, max_length=256)
    reference = models.CharField(null=True, max_length=128)
 
    environment = models.ForeignKey(env.Environment, related_name='projects', on_delete=models.CASCADE)

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
        facade_class = ProjectFacade

    def __str__(self):
        return "{} ({}:{})".format(self.name, self.type, self.name)


    def initialize(self, command):
        self.provider = command.get_provider('project', self.type, project = self)
        self.state = None
        return True
