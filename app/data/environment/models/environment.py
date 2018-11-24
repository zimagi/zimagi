
from systems import models


class EnvironmentFacade(models.ModelFacade):
    pass


class Environment(models.AppModel):
    name = models.CharField(primary_key=True, max_length=256)      

    class Meta:
        facade_class = EnvironmentFacade

    def  __str__(self):
        return "{}".format(self.name)
