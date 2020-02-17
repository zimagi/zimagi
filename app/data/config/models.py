from functools import lru_cache

from django.db import models as django

from settings import core as app_settings
from settings.roles import Roles
from data.state.models import State
from systems.models import fields, environment, group, provider
from utility.runtime import Runtime
from utility import data

import re
import yaml


class ConfigFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin,
):
    def ensure(self, command, reinit = False):
        if reinit or command.get_state('config_ensure', True):
            terminal_width = Runtime.width()

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
        if not value is None and instance.value_type in ('list', 'dict'):
            return self.encrypted_color(yaml.dump(value))
        else:
            return self.encrypted_color(value) if value else value

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
                        'name': setting,
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
    environment.EnvironmentModel
):
    value = fields.EncryptedDataField(null = True)
    value_type = django.CharField(max_length = 150, default = 'str')

    class Meta(environment.EnvironmentModel.Meta):
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
