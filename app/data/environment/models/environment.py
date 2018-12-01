
from systems import models
from data.environment.models import State


class EnvironmentFacade(models.ModelFacade):

    def env_key(self):
        return 'environment'

    def get_curr(self):
        return State.facade.retrieve(self.env_key())

    def set_curr(self, name):
        return State.facade.store(self.env_key(), value = name)

    def delete_curr(self):
        return State.facade.delete(self.env_key())


    def render(self, *fields, **filters):
        data = super().render(*fields, **filters)
        env = self.get_curr()

        data[0] = ['active'] + data[0]

        for index in range(1, len(data)):
            record = data[index]
            if env and record[0] == env.value:
                data[index] = ['*'] + data[index]
            else:
                data[index] = [''] + data[index]

        return data



class Environment(models.AppModel):
    
    name = models.CharField(primary_key=True, max_length=256)
    host = models.URLField(null=True)
    port = models.IntegerField(default=5120)
    token = models.CharField(null=True, max_length=40)     

    class Meta:
        facade_class = EnvironmentFacade

    def  __str__(self):
        return "{}".format(self.name)
