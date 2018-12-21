from .base import DataMixin
from data.environment import models


class EnvironmentMixin(DataMixin):

    def parse_env_name(self, optional = False):
        self._data_env = self._parse_variable(
            'environment', str,
            'environment name', 
            optional
        )

    @property
    def env_name(self):
        return self.options.get('environment', None)

    @property
    def env(self):
        self._data_env = self._load_instance(
            self._env, self.env_name, 
            self._data_env
        )
        return self._data_env


    def parse_env_fields(self, optional = False):
        self._parse_fields(self._env, 'env_fields', optional, ('created', 'updated'))

    @property
    def env_fields(self):
        return self.options.get('env_fields', {})


    @property
    def _state(self):
        return models.State.facade
    
    @property
    def _env(self):
        return models.Environment.facade


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
