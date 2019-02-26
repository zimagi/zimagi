from django.conf import settings

from . import DataMixin
from data.config.models import Config
from utility import config


class ConfigMixin(DataMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(stdout, stderr, no_color)
        self.facade_index['01_config'] = self._config


    def parse_config_provider_name(self, optional = False, help_text = 'environment configuration provider (default @config_provider|internal)'):
        self.parse_variable('config_provider_name', optional, str, help_text, 'NAME')

    @property
    def config_provider_name(self):
        name = self.options.get('config_provider_name', None)
        if not name:
            name = self.get_config('config_provider', required = False)
        if not name:
            name = config.Config.string('CONFIG_PROVIDER', 'internal')
        return name

    @property
    def config_provider(self):
        return self.get_provider('config', self.config_provider_name)


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


    def parse_config_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._config, 'config_fields', optional, (
                'created', 
                'updated',
                'environment',
                'type',
                'config',
                'variables',
                'state_config'
            ),
            help_callback
        )

    @property
    def config_fields(self):
        return self.options.get('config_fields', {})


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
    def _config(self):
        return self.facade(Config.facade)


    def get_config(self, name, default = None, required = False):
        if not name:
            return default
        
        config = self.get_instance(self._config, name, required = required)
        
        if config is None:
            return default
        
        return config.value
