
from systems.command import args
from data.environment import models


class EnvironmentMixin(object):

    def generate_schema(self):
        super().get_schema()
        self.schema['environment'] = 'str'


    def parse_env(self):
        self._data_env = None
        args.parse_var(self.parser, 'environment', str, 'environment name')

    @property
    def env_name(self):
        return self.options['environment']

    @property
    def env(self):
        if not self._data_env:
            self._data_env = self._env.retrieve(self.env_name)

            if not self._data_env:
                self.error("Environment {} does not exist".format(self.env_name))
        
        return self._data_env


    @property
    def _state(self):
        return models.State.facade
    
    @property
    def _env(self):
        return models.Environment.facade


    def get_env(self):
        return self._env.get_curr()

    def set_env(self, name):
        if not self._env.retrieve(name):
            self.error("Environment does not exist")

        state, created = self._env.set_curr(name)

        if created:
            self.success(" > Successfully created environment state")
        else:
            self.success(" > Successfully updated environment state")

    def delete_env(self):
        if self._env.delete_curr():
            self.success(" > Successfully deleted environment state")
        else:
            self.error("Environment state deletion failed")
