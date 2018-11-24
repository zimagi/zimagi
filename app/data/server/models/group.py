
from systems import models


class GroupFacade(models.ModelFacade):
    pass


class Group(models.AppModel):
    name = models.CharField(primary_key=True, max_length=256)
    parent = models.ForeignKey("Group", null=True, on_delete=models.CASCADE)

    class Meta:
        facade_class = GroupFacade
