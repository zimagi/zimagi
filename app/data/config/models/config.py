
from systems import models
from data.environment import models as env
from data.config import models as config


class ConfigFacade(models.ModelFacade):

    def get_packages(self):
        return super().get_packages() + ['environment', 'config']


    def key(self):
        return 'name'
 
    def scope(self, fields = False):
        if fields:
            return ('environment',)
        
        curr_env = env.Environment.facade.get_env()
        if not curr_env:
            return False

        return { 'environment_id': curr_env }


class Config(models.AppModel):
    name = models.CharField(max_length=256)      
    value = models.TextField(null=True)
    user = models.CharField(null=True, max_length=40)
    description = models.TextField(null=True)

    environment = models.ForeignKey(env.Environment, related_name='config', on_delete=models.CASCADE)
    groups = models.ManyToManyField(config.ConfigGroup, related_name='config', blank=True)

    class Meta:
        unique_together = ('environment', 'name')
        facade_class = ConfigFacade

    def  __str__(self):
        return "{} ({})".format(self.name, self.value)

    def initialize(self, command):
        groups = list(self.groups.values_list('name', flat = True))
        
        if groups and not command.check_access(groups):
            return False
        
        return True
