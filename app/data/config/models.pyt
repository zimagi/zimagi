from functools import lru_cache

from django.conf import settings
from django.db import models as django

from settings import core as app_settings
from settings.roles import Roles
from data.state.models import State
from data.mixins import provider
from data.environment import models as environment
from data.group import models as group
from systems.models import fields
from systems.models.facade import ModelFacade
from utility.runtime import Runtime
from utility import data

import re
import yaml


class ConfigModelFacadeMixin(ModelFacade):

    def get_field_config_display(self, instance, value, short):
        if not value:
            return ''
        else:
            return self.encrypted_color(yaml.dump(value).strip())


class ConfigMixin(django.Model):

    config = fields.EncryptedDataField(default = {}, editable = False)

    class Meta:
        abstract = True


class ConfigFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    environment.EnvironmentBaseFacadeMixin,
):
    def ensure(self, command, reinit = False):
        if reinit or command.get_state('config_ensure', True):
            terminal_width = command.display_width

            if not reinit:
                command.notice(
                    "\n".join([
                        "Loading MCMI system configurations",
                        "-" * terminal_width
                    ])
                )

            self.clear(groups__name = 'system')
            command.config_provider.store('environment', {
                    'value': command._environment.get_env(),
                    'value_type': 'str'
                },
                groups = ['system']
            )
            for setting in self.get_settings():
                command.config_provider.store(setting['name'], {
                        'value': setting['value'],
                        'value_type': setting['type']
                    },
                    groups = ['system']
                )
            command.set_state('config_ensure', False)

            if not reinit:
                command.notice("-" * terminal_width)

    def keep(self):
        keep = ['environment']
        for setting in self.get_settings():
            keep.append(setting['name'])
        return keep


    def get_field_value_display(self, instance, value, short):
        if value is not None and instance.value_type in ('list', 'dict'):
            return self.encrypted_color(yaml.dump(value))
        else:
            return self.encrypted_color(str(value))

    def get_field_value_type_display(self, instance, value, short):
        return value


    @lru_cache(maxsize = None)
    def get_settings(self):
        settings_variables = []
        for setting in dir(app_settings):
            if setting == setting.upper():
                value = getattr(app_settings, setting)
                value_type = type(value).__name__

                if value_type in ('bool', 'int', 'float', 'str', 'list', 'dict'):
                    settings_variables.append({
                        'name': "{}_{}".format(settings.APP_SERVICE, setting),
                        'value': value,
                        'type': value_type
                    })
        return settings_variables

    def clear(self, **filters):
        result = super().clear(**filters)
        State.facade.store('config_ensure', value = True)
        return result


class Config(
    provider.ProviderMixin,
    group.GroupMixin,
    environment.EnvironmentBase
):
    value = fields.EncryptedDataField(null = True)
    value_type = django.CharField(max_length = 150, default = 'str')

    class Meta(environment.EnvironmentBase.Meta):
        verbose_name = "config"
        verbose_name_plural = "configs"
        facade_class = ConfigFacade
        ordering = ['name']
        provider_name = 'config'

    def allowed_groups(self):
        return [ Roles.admin ]

    def save(self, *args, **kwargs):
        self.value = data.format_value(self.value_type, self.value)
        super().save(*args, **kwargs)
        State.facade.store('config_ensure', value = True)
