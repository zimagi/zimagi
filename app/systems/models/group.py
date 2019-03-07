from settings import Roles
from django.db import models as django

from data.group.models import Group
from .base import ModelFacade


class GroupModelFacadeMixin(ModelFacade):

    def check_group_access(self, instance, command):
        with self.thread_lock:
            groups = list(instance.allowed_groups()) + list(instance.groups.all().values_list('name', flat = True))
            if groups and not command.check_access(groups):
                return False
        return True

    def get_field_groups_display(self, instance, value, short):
        groups = [ str(x) for x in value.all() ]
        return "\n".join(groups)


class GroupMixin(django.Model):

    groups = django.ManyToManyField(Group,
        related_name = "%(class)s_relation"
    )
    class Meta:
        abstract = True

    def allowed_groups(self):
        return [ Roles.admin ]

    def initialize(self, command):
        if getattr(super(), 'initialize', None):
            if not super().initialize(command):
                return False
        return self.facade.check_group_access(self, command)
