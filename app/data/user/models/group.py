from django.conf import settings
from django.db import models
from django.contrib.auth import models as user_models

from settings import Roles
from systems import models


class GroupFacade(models.ModelFacade):

    def get_packages(self):
        return super().get_packages() + ['user', 'group']


    def ensure(self, env, user):
        admin_group = self.retrieve(Roles.admin)

        if not admin_group:
            (admin_group, created) = self.store(Roles.admin)
            user.admin.groups.add(admin_group)


    def key(self):
        return 'name'


class Group(user_models.Group, metaclass = models.AppMetaModel):

    class Meta:
        proxy = True
        facade_class = GroupFacade
