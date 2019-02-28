from django.db import models as django

from settings import Roles
from systems.models import environment, provider


class GroupFacade(
    provider.ProviderModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    def ensure(self, command):
        admin_group = self.retrieve(Roles.admin)
        if not admin_group:
            admin_group = command.group_provider.create(Roles.admin, {})
            command._user.admin.groups.add(admin_group)

    def get_provider_name(self):
        return 'group'

    
    def get_relations(self):
        return {
            'parent': ('group_parent_name', '--parent')
        }

    def default_order(self):
        return 'name'

    def get_list_fields(self):
        return (
            ('name', 'ID'),
            ('type', 'Type'),
            ('created', 'Created'),
            ('updated', 'Updated')                    
        )
    
    def get_display_fields(self):
        return (
            ('name', 'ID'),
            ('environment', 'Environment'),
            ('type', 'Type'),
            ('parent', 'Parent'),
            '---',
            ('created', 'Created'),
            ('updated', 'Updated')
        )
    
    def get_field_parent_display(self, instance, value, short):
        return str(value)


class Group(
    provider.ProviderMixin,
    environment.EnvironmentModel
):
    parent = django.ForeignKey("Group", null=True, on_delete=django.SET_NULL)
    
    class Meta(environment.EnvironmentModel.Meta):
        facade_class = GroupFacade

    def __str__(self):
        if self.parent:
            return "{} ({})".format(self.name, self.parent)
        return self.name
