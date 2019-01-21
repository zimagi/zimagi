from django.conf import settings

from . import DataMixin
from data.config import models


class ConfigMixin(DataMixin):

    def parse_config_name(self, optional = False, help_text = 'environment configuration name'):
        self.parse_variable('config', optional, str, help_text)

    @property
    def config_name(self):
        return self.options.get('config', None)

    @property
    def config(self):
        return self.get_instance(self._config, self.config_name)


    def parse_config_value(self, optional = False, help_text = 'environment configuration value'):
        self.parse_variable('config_value', optional, str, help_text)

    @property
    def config_value(self):
        return self.options.get('config_value', None)


    def parse_config_fields(self, optional = False):
        self.parse_fields(self._config, 'config_fields', optional, ('created', 'updated'))

    @property
    def config_fields(self):
        return self.options.get('config_fields', {})


    @property
    def _config(self):
        return models.Config.facade


    def required_config(self, name):
        config = self.get_instance(self._config, name)
        return config.value

    def optional_config(self, name, default = None):
        config = self.get_instance(self._config, name, error_on_not_found = False)
        
        if not config:
            return default
        
        return config.value
