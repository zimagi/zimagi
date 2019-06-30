from django.conf import settings

from data.environment.models import Environment
from data.host.models import Host
from data.state.models import State
from .base import DataMixin


class EnvironmentMixin(DataMixin):

    schema = {
        'state': {
            'model': State
        },
        'environment': {
            'model': Environment,
            'provider': True,
            'provider_config': False,
            'name_default': 'curr_env_name'
        },
        'host': {
            'model': Host,
            'name_default': settings.DEFAULT_HOST_NAME
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['00_environment'] = self._environment
        self.facade_index['01_host'] = self._host
        self.facade_index['01_state'] = self._state


    @property
    def curr_env_name(self):
        return self._environment.get_env()


    def parse_environment_repo(self, optional = False, help_text = 'environment runtime repository'):
        self.parse_variable('repo', optional, str, help_text,
            value_label = 'HOST',
            default = settings.DEFAULT_RUNTIME_REPO
        )

    @property
    def environment_repo(self):
        return self.options.get('repo', None)

    def parse_environment_image(self, optional = False, help_text = 'environment runtime image ({})'.format(settings.DEFAULT_RUNTIME_IMAGE)):
        self.parse_variable('image', optional, str, help_text,
            value_label = 'REFERENCE',
            default = settings.DEFAULT_RUNTIME_IMAGE
        )

    @property
    def environment_image(self):
        image = self.options.get('image', None)
        if not image:
            image = settings.DEFAULT_RUNTIME_IMAGE
        return image


    def get_env(self, host_name = None):
        name = self._environment.get_env()
        env = self.get_instance(self._environment, name, required = False)

        if not host_name:
            host_name = self.environment_host

        host = self._host.retrieve(host_name)
        env.host = host.host if host else None
        env.port = host.port if host else None
        env.user = host.user if host else None
        env.token = host.token if host else None
        return env

    def create_env(self, name, **fields):
        env = self._environment.create(name)
        host = self._host.create('temp')

        env.host = host.host
        env.port = host.port
        env.user = host.user
        env.token = host.token

        for field, value in fields.items():
            setattr(env, field, value)
        return env

    def set_env(self, name = None, repo = None, image = None):
        self._environment.set_env(name, repo, image)
        self.success("Successfully updated current environment")

    def update_env_host(self, **fields):
        name = fields.pop('name', None)
        if not name:
            name = self.environment_host

        host = self._host.retrieve(name)
        if not host:
            host = self._host.create(name, **fields)
        else:
            for field, value in fields.items():
                setattr(host, field, value)
        host.save()

    def delete_env(self):
        self._environment.delete_env()
        self.success("Successfully removed environment")


    def get_state(self, name, default = None):
        instance = self.get_instance(self._state, name, required = False)
        if instance:
            return instance.value
        return default

    def set_state(self, name, value = None):
        self._state.store(name, value = value)

    def delete_state(self, name = None):
        self._state.delete(name)

    def clear_state(self):
        self._state.clear()
