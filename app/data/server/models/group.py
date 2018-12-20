
from systems import models


class ServerGroupFacade(models.ModelFacade):
    pass


class ServerGroup(models.AppModel):
    name = models.CharField(primary_key=True, max_length=256)
    
    class Meta:
        facade_class = ServerGroupFacade
