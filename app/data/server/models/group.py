from systems import models


class ServerGroupFacade(models.ModelFacade):
    pass


class ServerGroup(models.AppModel):
    name = models.CharField(primary_key=True, max_length=256)
    parent = models.ForeignKey("ServerGroup", null=True, on_delete=models.SET_NULL)
    
    class Meta:
        facade_class = ServerGroupFacade

    def __str__(self):
        if self.parent:
            return "{} ({})".format(self.name, self.parent)
        return self.name
