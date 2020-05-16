from django.db import models as django

from settings.roles import Roles
from data.state.models import State
from data.environment import models as environment
from data.mixins import provider
from systems.models.facade import ModelFacade
from .cache import Cache

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

    groups = django.ManyToManyField('Group',
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


class GroupFacade(
    provider.ProviderModelFacadeMixin,
    environment.EnvironmentBaseFacadeMixin
):
    def ensure(self, command):
        if command.get_state('group_ensure', True):
            admin_group = self.retrieve(Roles.admin)
            if not admin_group:
                admin_group = command.group_provider.create(Roles.admin, {})

            for role, description in Roles.index.items():
                if role != 'admin':
                    group = self.retrieve(role)
                    if not group:
                        group = command.group_provider.create(role)
                        group.parent = admin_group
                        group.save()

            command._user.admin.groups.add(admin_group)
            command.set_state('group_ensure', False)

    def keep(self):
        return list(Roles.index.keys())

    def get_field_parent_display(self, instance, value, short):
        return self.relation_color(str(value))


class Group(
    provider.ProviderMixin,
    environment.EnvironmentBase
):
    parent = django.ForeignKey("Group",
        null = True,
        on_delete = django.SET_NULL,
        related_name = "%(class)s_relation",
        editable = False
    )

    class Meta(environment.EnvironmentBase.Meta):
        verbose_name = "group"
        verbose_name_plural = "groups"
        facade_class = GroupFacade
        ordering = ['name']
        provider_name = 'group'

    def __str__(self):
        if self.parent:
            return "{} ({})".format(self.name, self.parent)
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        State.facade.store('group_ensure', value = True)
