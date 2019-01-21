
from systems import models


class ConfigGroupFacade(models.ModelFacade):

    def get_packages(self):
        return super().get_packages() + ['environment', 'config', 'group']


class ConfigGroup(models.AppModel):
    name = models.CharField(primary_key=True, max_length=256)
    
    class Meta:
        facade_class = ConfigGroupFacade
