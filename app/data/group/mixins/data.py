from settings.roles import Roles
from django.db import models as django

from data.group.models import Group
from data.group.cache import Cache
from .base import ModelFacade

import threading


class GroupModelFacadeMixin(ModelFacade):

    def check_group_access(self, instance, command):
        if not command.check_access(instance):
            return False
        return True

    def get_field_groups_display(self, instance, value, short):
        groups = [ str(x) for x in value.all() ]
        return self.relation_color("\n".join(groups))


class GroupMixin(django.Model):

    group_lock = threading.Lock()

    groups = django.ManyToManyField(Group,
        related_name = "%(class)s_relations"
    )
    class Meta:
        abstract = True


    def access_groups(self, reset = False):
        return self.allowed_groups() + self.group_names(reset)

    def allowed_groups(self):
        return [ Roles.admin ]

    def group_names(self, reset = False):
        with self.group_lock:
            # This can still get wonky somehow with heavy parallelism
            return Cache().get(self.facade, self.id,
                reset = reset
            )


    def save(self, *args, **kwargs):
        Cache().clear(self.facade)
        super().save(*args, **kwargs)


    def initialize(self, command):
        if getattr(super(), 'initialize', None):
            if not super().initialize(command):
                return False
        return self.facade.check_group_access(self, command)
