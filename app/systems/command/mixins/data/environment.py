from django.conf import settings

from . import DataMixin
from data.environment.models import Environment
from data.state.models import State
from utility import config


class EnvironmentMixin(DataMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['00_env'] = self._env
        self.facade_index['01_state'] = self._state


    def parse_env_provider_name(self, optional = False, help_text = 'system environment provider (default @env_provider|internal)'):
        self.parse_variable('env_provider_name', optional, str, help_text, 'NAME')

    @property
    def env_provider_name(self):
        name = self.options.get('env_provider_name', None)
        if not name:
            name = self.get_config('env_provider', required = False)
        if not name:
            name = config.Config.string('ENV_PROVIDER', 'internal')
        return name

    @property
    def env_provider(self):
        return self.get_provider('env', self.env_provider_name)


    def parse_env_name(self, optional = False, help_text = 'environment name'):
        self.parse_variable('environment', optional, str, help_text, 'NAME')

    @property
    def env_name(self):
        return self.options.get('environment', self.curr_env_name)
    
    @property
    def curr_env_name(self):
        return self._env.get_env()

    @property
    def env(self):
        return self.get_instance(self._env, self.env_name)


    def parse_env_repo(self, optional = False, help_text = 'environment runtime repository'):
        self.parse_variable('repo', optional, str, help_text, 'HOST', settings.DEFAULT_RUNTIME_REPO)

    @property
    def env_repo(self):
        return self.options.get('repo', None)

    def parse_env_image(self, optional = False, help_text = 'environment runtime image ({})'.format(settings.DEFAULT_RUNTIME_IMAGE)):
        self.parse_variable('image', optional, str, help_text, 'REFERENCE', settings.DEFAULT_RUNTIME_IMAGE)

    @property
    def env_image(self):
        image = self.options.get('image', None)
        if not image:
            image = settings.DEFAULT_RUNTIME_IMAGE
        return image


    def parse_env_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._env, 'env_fields', optional, (
                'created', 
                'updated',
                'type',
                'config',
                'variables',
                'state_config'
            ),
            help_callback
        )

    @property
    def env_fields(self):
        return self.options.get('env_fields', {})


    def parse_env_order(self, optional = '--order', help_text = 'environment ordering fields (~field for desc)'):
        self.parse_variables('env_order', optional, str, help_text, '[~]FIELD')

    @property
    def env_order(self):
        return self.options.get('env_order', [])


    def parse_env_search(self, optional = True, help_text = 'environment search fields'):
        self.parse_variables('env_search', optional, str, help_text, 'REFERENCE')

    @property
    def env_search(self):
        return self.options.get('env_search', [])

    @property
    def env_instances(self):
        return self.search_instances(self._env, self.env_search)

     
    @property
    def _env(self):
        return self.facade(Environment.facade)

    @property
    def _state(self):
        return self.facade(State.facade)


    def get_env(self, name = None):
        if not name:
            name = self._env.get_env()
        return self.get_instance(self._env, name, required = False)

    def set_env(self, name = None, repo = None, image = None):
        self._env.set_env(name, repo, image)
        self.success("Successfully updated current environment")

    def delete_env(self):
        self._state.clear()
        self._env.delete_env()
        self.success("Successfully removed environment")


    def get_state(self, name, default = None):
        instance = self.get_instance(self._state, name, required = False)
        if instance:
            return instance.value
        return default

    def set_state(self, name, value = None):
        self._state.store(name, value = value)

    def delete_state(self, name = None):
        if not self._state.delete(name):
            self.error("Environment state change failed")
