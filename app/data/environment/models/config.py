
from systems import models
from . import environment as env


class ConfigFacade(models.ModelFacade):

    def get_packages(self):
        return super().get_packages() + ['environment', 'config']


    def key(self):
        return 'name'
 
    def scope(self, fields = False):
        if fields:
            return ('environment',)
        
        state = env.Environment.facade.get_curr()
        if not state:
            return False

        return { 'environment_id': state.value }


class Config(models.AppModel):
    name = models.CharField(max_length=256)      
    value = models.TextField()

    environment = models.ForeignKey(env.Environment, related_name='config', on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('environment', 'name')
        facade_class = ConfigFacade

    def  __str__(self):
        return "{} ({})".format(self.name, self.value)
