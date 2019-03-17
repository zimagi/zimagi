from django.conf import settings
from django.db import models as django

from settings.roles import Roles
from systems.models import environment, group, provider

import os


class ModuleFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    def ensure(self, command):
        if not self.retrieve(settings.CORE_MODULE):
            command.options.add('module_provider_name', 'sys_internal')
            command.module_provider.create(settings.CORE_MODULE, {})

    def keep(self):
        return settings.CORE_MODULE

    def get_provider_name(self):
        return 'module'

    def get_relations(self):
        return {
            'groups': ('group', 'Groups', '--groups')
        }

    def default_order(self):
        return 'name'

    def get_list_fields(self):
        return (
            ('name', 'Name'),
            ('type', 'Type'),
            ('status', 'Status'),
            ('remote', 'Remote'),
            ('reference', 'Reference')
        )

    def get_display_fields(self):
        return (
            ('name', 'Name'),
            ('environment', 'Environment'),
            ('type', 'Type'),
            ('status', 'Status'),
            '---',
            ('config', 'Configuration'),
            '---',
            ('remote', 'Remote'),
            ('reference', 'Reference'),
            '---',
            ('created', 'Created'),
            ('updated', 'Updated')
        )

    def get_field_remote_display(self, instance, value, short):
        return value

    def get_field_reference_display(self, instance, value, short):
        return value

    def get_field_status_display(self, instance, value, short):
        path = instance.provider.module_path(instance.name, ensure = False)
        cenv_path = os.path.join(path, 'cenv.yml')

        if os.path.isfile(cenv_path):
            return 'valid'
        return 'invalid'


class Module(
    provider.ProviderMixin,
    group.GroupMixin,
    environment.EnvironmentModel
):
    remote = django.CharField(null=True, max_length=256)
    reference = django.CharField(null=True, max_length=128)

    class Meta(environment.EnvironmentModel.Meta):
        facade_class = ModuleFacade

    def allowed_groups(self):
        return [ Roles.admin, Roles.module_admin ]
