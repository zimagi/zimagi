
from systems import models
from data.environment import models as env


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

    environment = models.ForeignKey(env.Environment, related_name='config', on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('environment', 'name')
        facade_class = ConfigFacade

    def  __str__(self):
        return "{} ({})".format(self.name, self.value)
