from django.db import models as django

from settings.roles import Roles
from data.state.models import State
from systems.models import environment, provider


class GroupFacade(
    provider.ProviderModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
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
    environment.EnvironmentModel
):
    parent = django.ForeignKey("Group", null=True, on_delete=django.SET_NULL)

    class Meta(environment.EnvironmentModel.Meta):
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
