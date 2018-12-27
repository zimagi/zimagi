
from systems import models


class StateFacade(models.ModelFacade):

    def get_packages(self):
        return super().get_packages() + ['environment', 'state']


class State(models.AppModel):
    name = models.CharField(primary_key=True, max_length=256)      
    value = models.TextField()
    
    class Meta:
        facade_class = StateFacade

    def  __str__(self):
        return "{} ({})".format(self.name, self.value)
