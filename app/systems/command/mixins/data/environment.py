from django.conf import settings

from .base import DataMixin
from data.environment import models


class EnvironmentMixin(DataMixin):

    def parse_env_name(self, optional = False, help_text = 'environment name'):
        self._parse_variable('environment', optional, str, help_text)

    @property
    def env_name(self):
        return self.options.get('environment', None)

    @property
    def env(self):
        self._data_env = self._load_instance(
            self._env, self.env_name, 
            getattr(self, '_data_env', None)
        )
        return self._data_env


    def parse_env_repo(self, optional = False, help_text = 'environment runtime repository'):
        self._parse_variable('repo', optional, str, help_text)

    @property
    def env_repo(self):
        return self.options.get('repo', None)

    def parse_env_image(self, optional = False, help_text = 'environment runtime image ({})'.format(settings.DEFAULT_RUNTIME_IMAGE)):
        self._parse_variable('image', optional, str, help_text)

    @property
    def env_image(self):
        image = self.options.get('image', None)
        if not image:
            image = settings.DEFAULT_RUNTIME_IMAGE
        return image


    def parse_env_fields(self, optional = False):
        self._parse_fields(self._env, 'env_fields', optional, ('created', 'updated'))

    @property
    def env_fields(self):
        return self.options.get('env_fields', {})


    def parse_config_name(self, optional = False, help_text = 'environment configuration name'):
        self._parse_variable('config', optional, str, help_text)

    @property
    def config_name(self):
        return self.options.get('config', None)

    @property
    def config(self):
        self._data_config = self._load_instance(
            self._config, self.config_name, 
            getattr(self, '_data_config', None)
        )
        return self._data_config


    def parse_config_value(self, optional = False, help_text = 'environment configuration value'):
        self._parse_variable('config_value', optional, str, help_text)

    @property
    def config_value(self):
        return self.options.get('config_value', None)


    def parse_config_fields(self, optional = False):
        self._parse_fields(self._config, 'config_fields', optional, ('created', 'updated'))

    @property
    def config_fields(self):
        return self.options.get('config_fields', {})


    @property
    def _state(self):
        return models.State.facade
    
    @property
    def _env(self):
        return models.Environment.facade

    @property
    def _config(self):
        return models.Config.facade


    def get_env(self, name = None):
        if not name:
            name = self._env.get_env()
        
        if name:
            return self._env.retrieve(name)
        return None

    def set_env(self, name, repo = None, image = None):
        self._env.set_env(name, repo, image)
        self.success("Successfully updated environment state")

    def delete_env(self, name = None):
        if self._env.delete_env(name):
            self.success("Successfully removed environment")
        else:
            self.error("Environment state change failed")


    def required_config(self, name):
        config = self._load_instance(self._config, name)
        return config.value

    def optional_config(self, name, default = None):
        config = self._config.retrieve(name)
        
        if not config:
            return default
        
        return config.value
