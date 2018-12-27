
from django.db import models
from django.contrib.auth import models as user_models

from systems import models


class GroupFacade(models.ModelFacade):

    def get_packages(self):
        return super().get_packages() + ['user', 'group']


    def key(self):
        return 'name'


class Group(user_models.Group, metaclass = models.AppMetaModel):

    class Meta:
        proxy = True
        facade_class = GroupFacade
