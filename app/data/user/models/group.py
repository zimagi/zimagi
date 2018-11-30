
from django.db import models
from django.contrib.auth import models as user_models

from systems import models


class GroupFacade(models.ModelFacade):

    def key(self):
        return 'name'


class Group(user_models.Group, metaclass = models.AppMetaModel):

    class Meta:
        proxy = True
        facade_class = GroupFacade
