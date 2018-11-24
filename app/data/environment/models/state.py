
from systems import models


class StateFacade(models.ModelFacade):

    def env_key(self):
        return 'environment'

    def get_env(self):
        return self.retrieve(self.env_key())

    def set_env(self, name):
        return self.store(self.env_key(), value = name)

    def clear_env(self):
        return self.delete(self.env_key())


class State(models.AppModel):
    name = models.CharField(primary_key=True, max_length=256)      
    value = models.TextField()
    
    class Meta:
        facade_class = StateFacade

    def  __str__(self):
        return "{} ({})".format(self.name, self.value)
