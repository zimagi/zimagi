from settings import Roles
from django.db import models as django

from data.group.models import Group
from .base import ModelFacade


class GroupModelFacadeMixin(ModelFacade):
    pass


class GroupMixin(django.Model):

    groups = django.ManyToManyField(Group, related_name='+')

    class Meta:
        abstract = True

    def allowed_groups(self):
        # Override in subclass
        return []

    def initialize(self, command):
        if getattr(super(), 'initialize', None):
            if not super().initialize(command):
                return False
               
        groups = list(self.allowed_groups()) + list(self.groups.all().values_list('name', flat = True))
        if groups and not command.check_access(groups):
            return False
        return True
