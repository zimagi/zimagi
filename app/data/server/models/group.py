
from systems import models


class ServerGroupFacade(models.ModelFacade):

    def get_packages(self):
        return super().get_packages() + ['server', 'group']


class ServerGroup(models.AppModel):
    name = models.CharField(primary_key=True, max_length=256)
    
    class Meta:
        facade_class = ServerGroupFacade
