from django.db import models as django

from settings.roles import Roles
from systems.models import fields, environment, group, provider
from utility import data

import re
import yaml


class ConfigFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin,
):
    def get_provider_name(self):
        return 'config'

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
            ('value_type', 'Value type'),
            ('value', 'Value')
        )

    def get_display_fields(self):
        return (
            ('name', 'Name'),
            ('environment', 'Environment'),
            ('type', 'Type'),
            '---',
            ('value_type', 'Value type'),
            ('value', 'Value'),
            '---',
            ('created', 'Created'),
            ('updated', 'Updated')
        )

    def get_field_value_display(self, instance, value, short):
        return self.encrypted_color(re.sub('\s?\.\.\.\s?$', '', yaml.dump(value, default_flow_style=False)))

    def get_field_value_type_display(self, instance, value, short):
        return value


class Config(
    provider.ProviderMixin,
    group.GroupMixin,
    environment.EnvironmentModel
):
    value = fields.EncryptedDataField(null=True)
    value_type = django.CharField(max_length=150, default='str')

    class Meta(environment.EnvironmentModel.Meta):
        facade_class = ConfigFacade

    def allowed_groups(self):
        return [ Roles.admin ]

    def save(self, *args, **kwargs):
        self.value = data.format_value(self.value_type, self.value)
        super().save(*args, **kwargs)
