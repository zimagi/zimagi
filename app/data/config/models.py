from django.db import models as django

from settings import Roles
from systems.models import fields, environment, group, provider


class ConfigFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin,
):
    def get_provider_name(self):
        return 'config'


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
