from django.conf import settings

from . import DataMixin
from data.environment import models


class EnvironmentMixin(DataMixin):

    def parse_env_name(self, optional = False, help_text = 'environment name'):
        self.parse_variable('environment', optional, str, help_text)

    @property
    def env_name(self):
        return self.options.get('environment', None)

    @property
    def env(self):
        return self.get_instance(self._env, self.env_name)


    def parse_env_repo(self, optional = False, help_text = 'environment runtime repository'):
        self.parse_variable('repo', optional, str, help_text)

    @property
    def env_repo(self):
        return self.options.get('repo', None)

    def parse_env_image(self, optional = False, help_text = 'environment runtime image ({})'.format(settings.DEFAULT_RUNTIME_IMAGE)):
        self.parse_variable('image', optional, str, help_text)

    @property
    def env_image(self):
        image = self.options.get('image', None)
        if not image:
            image = settings.DEFAULT_RUNTIME_IMAGE
        return image


    def parse_env_fields(self, optional = False):
        self.parse_fields(self._env, 'env_fields', optional, ('created', 'updated'))

    @property
    def env_fields(self):
        return self.options.get('env_fields', {})


    @property
    def _state(self):
        return models.State.facade
    
    @property
    def _env(self):
        return models.Environment.facade


    def get_env(self, name = None):
        if not name:
            name = self._env.get_env()
        
        if name:
            return self.get_instance(self._env, name)
        
        return None

    def set_env(self, name, repo = None, image = None):
        self._env.set_env(name, repo, image)
        self.success("Successfully updated environment state")

    def delete_env(self, name = None):
        if self._env.delete_env(name):
            self.success("Successfully removed environment")
        else:
            self.error("Environment state change failed")
