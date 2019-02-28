from django.db import models as django

from settings import Roles
from systems.models import fields, environment, group, provider

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
            'groups': ('group_names', '--groups')
        }

    def default_order(self):
        return 'name'

    def get_list_fields(self):
        return (
            ('name', 'Name'),
            ('type', 'Type'),
            ('value', 'Value'),
            ('created', 'Created'),
            ('updated', 'Updated')            
        )
    
    def get_display_fields(self):
        return (
            ('name', 'Name'),
            ('environment', 'Environment'),
            ('type', 'Type'),
            '---',
            ('value', 'Value'),
            '---',
            ('created', 'Created'),
            ('updated', 'Updated')
        )
    
    def get_field_value_display(self, instance, value, short):
        return str(value)
    

class Config(
    provider.ProviderMixin,
    group.GroupMixin,
    environment.EnvironmentModel
):
    value = fields.EncryptedDataField(null=True)
    
    class Meta(environment.EnvironmentModel.Meta):
        facade_class = ConfigFacade

    def allowed_groups(self):
        return [ Roles.admin ]
