
from systems import models
from data.environment.models import State


class EnvironmentFacade(models.ModelFacade):

    def env_key(self):
        return 'environment'

    def get_curr(self):
        return State.facade.retrieve(self.env_key())

    def set_curr(self, name):
        return State.facade.store(self.env_key(), value = name)

    def clear_curr(self):
        return State.facade.delete(self.env_key())


class Environment(models.AppModel):
    name = models.CharField(primary_key=True, max_length=256)      

    class Meta:
        facade_class = EnvironmentFacade

    def  __str__(self):
        return "{}".format(self.name)
