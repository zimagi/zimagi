from systems import models
from data.environment.models import State


class EnvironmentFacade(models.ModelFacade):

    @property
    def default_env_name(self):
        return 'default'

    def ensure_env(self):
        curr_env = self.get_curr()

        if not curr_env:
            if not self.retrieve(self.default_env_name):
                self.store(self.default_env_name)

            self.set_curr()


    def env_key(self):
        return 'environment'

    def get_curr(self):
        return State.facade.retrieve(self.env_key())

    def set_curr(self, name = None):
        if name is None:
            name = self.default_env_name
        return State.facade.store(self.env_key(), value = name)

    def delete_curr(self):
        return self.set_curr()


    def render(self, *fields, **filters):
        data = super().render(*fields, **filters)
        env = self.get_curr()

        data[0] = ['active'] + data[0]

        for index in range(1, len(data)):
            record = data[index]
            if env and record[0] == env.value:
                data[index] = ['******'] + data[index]
            else:
                data[index] = [''] + data[index]

        return data


class Environment(models.AppModel):
    
    name = models.CharField(primary_key=True, max_length=256)
    host = models.URLField(null=True)
    port = models.IntegerField(default=5123)
    token = models.CharField(null=True, max_length=40)     

    class Meta:
        facade_class = EnvironmentFacade

    def  __str__(self):
        return "{}".format(self.name)
