from django.conf import settings

from . import DataMixin
from data.config import models


class ConfigMixin(DataMixin):

    def parse_config_name(self, optional = False, help_text = 'environment configuration name'):
        self.parse_variable('config', optional, str, help_text, 'NAME')

    @property
    def config_name(self):
        return self.options.get('config', None)

    @property
    def config(self):
        return self.get_instance(self._config, self.config_name)


    def parse_config_value(self, optional = False, help_text = 'environment configuration value'):
        self.parse_variable('config_value', optional, str, help_text, 'VALUE')

    @property
    def config_value(self):
        return self.options.get('config_value', None)


    def parse_config_fields(self, optional = False):
        self.parse_fields(self._config, 'config_fields', optional, ('created', 'updated'))

    @property
    def config_fields(self):
        return self.options.get('config_fields', {})


    def parse_config_group(self, optional = False, help_text = 'environment configuration group'):
        self.parse_variable('config_group', optional, str, help_text, 'NAME')

    @property
    def config_group_name(self):
        return self.options.get('config_group', None)

    @property
    def config_group(self):
        return self.get_instance(self._config_group, self.config_group_name)


    def parse_config_groups(self, flag = '--groups', help_text = 'one or more configuration group names'):
        self.parse_variables('config_groups', flag, str, help_text, 'NAME')

    @property
    def config_group_names(self):
        return self.options.get('config_groups', [])

    @property
    def config_groups(self):
        return self.get_instances(self._config_group, 
            names = self.config_group_names
        )


    def parse_config_reference(self, optional = False, help_text = 'unique environment configuration or group name'):
        self.parse_variable('config_reference', optional, str, help_text, 'REFERENCE')

    @property
    def config_reference(self):
        return self.options.get('config_reference', None)

    @property
    def configs(self):
        return self.get_instances_by_reference(self._config, 
            self.config_reference,
            group_facade = self._config_group
        )


    @property
    def _config_group(self):
        return self.facade(models.ConfigGroup.facade)

    @property
    def _config(self):
        return self.facade(models.Config.facade)


    def get_config(self, name, default = None, required = False):
        if not name:
            return default
        
        config = self.get_instance(self._config, name, required = required)
        
        if config is None:
            return default
        
        return config.value
