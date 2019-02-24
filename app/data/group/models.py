from django.db import models as django

from settings import Roles
from systems.models import environment


class GroupFacade(
    environment.EnvironmentModelFacadeMixin
):
    def ensure(self, env, user):
        admin_group = self.retrieve(Roles.admin)

        if not admin_group:
            (admin_group, created) = self.store(Roles.admin)
            user.admin.groups.add(admin_group)


class Group(
    environment.EnvironmentModel
):
    parent = django.ForeignKey("Group", null=True, on_delete=django.SET_NULL)
    
    class Meta(environment.EnvironmentModel.Meta):
        facade_class = GroupFacade

    def __str__(self):
        if self.parent:
            return "{} ({})".format(self.name, self.parent)
        return self.name
