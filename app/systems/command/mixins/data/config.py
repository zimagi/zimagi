from django.conf import settings

from . import DataMixin
from data.config.models import Config
from utility import config


class ConfigMixin(DataMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['01_config'] = self._config


    def parse_config_provider_name(self, optional = False, help_text = 'environment configuration provider (default @config_provider|internal)'):
        self.parse_variable('config_provider_name', optional, str, help_text, 
            value_label = 'NAME'
        )

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
        self.parse_variable('config', optional, str, help_text, 
            value_label = 'NAME'
        )

    @property
    def config_name(self):
        return self.options.get('config', None)

    @property
    def config(self):
        return self.get_instance(self._config, self.config_name)


    def parse_config_value(self, optional = False, help_text = 'environment configuration value'):
        self.parse_variable('config_value', optional, str, help_text, 
            value_label = 'VALUE'
        )

    @property
    def config_value(self):
        return self.options.get('config_value', None)


    def parse_config_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._config, 'config_fields', 
            optional = optional, 
            excluded_fields = (
                'created', 
                'updated',
                'environment',
                'type',
                'config',
                'variables',
                'state_config'
            ),
            help_callback = help_callback
        )

    @property
    def config_fields(self):
        return self.options.get('config_fields', {})

    @property
    def configs(self):
        return self.get_instances_by_reference(self._config, 
            self.config_reference,
            group_facade = self._config_group
        )


    def parse_config_order(self, optional = '--order', help_text = 'configuration ordering fields (~field for desc)'):
        self.parse_variables('config_order', optional, str, help_text, 
            value_label = '[~]FIELD'
        )

    @property
    def config_order(self):
        return self.options.get('config_order', [])


    def parse_config_search(self, optional = True, help_text = 'configuration search fields'):
        self.parse_variables('config_search', optional, str, help_text, 
            value_label = 'REFERENCE'
        )

    @property
    def config_search(self):
        return self.options.get('config_search', [])

    @property
    def config_instances(self):
        return self.search_instances(self._config, self.config_search)


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
