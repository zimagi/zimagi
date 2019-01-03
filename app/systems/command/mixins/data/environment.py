from .base import DataMixin
from data.environment import models


class EnvironmentMixin(DataMixin):

    def parse_env_name(self, optional = False, help_text = 'environment name'):
        self._parse_variable('environment', str, help_text, optional)

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


    def parse_env_fields(self, optional = False):
        self._parse_fields(self._env, 'env_fields', optional, ('created', 'updated'))

    @property
    def env_fields(self):
        return self.options.get('env_fields', {})


    def parse_config_name(self, optional = False, help_text = 'environment configuration name'):
        self._parse_variable('config', str, help_text, optional)

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
        self._parse_variable('config_value', str, help_text, optional)

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


    def get_env(self):
        environment = self._env.get_curr()
        if environment:
            return self._load_instance(self._env, environment.value)
        return None

    def set_env(self, name):
        self._load_instance(self._env, name)
        state, created = self._env.set_curr(name)
        self.success("Successfully updated environment state")

    def delete_env(self):
        if self._env.delete_curr():
            self.success("Successfully switched to default environment")
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
