from systems import models


class ConfigGroupFacade(models.ModelFacade):
    pass

class ConfigGroup(models.AppModel):
    name = models.CharField(primary_key=True, max_length=256)
    
    class Meta:
        facade_class = ConfigGroupFacade
