
from systems.command import args
from data.environment import models
from utility import text


class EnvironmentMixin(object):

    def generate_schema(self):
        super().get_schema()
        self.schema['environment'] = 'str'
        self.schema['env_fields'] = 'dict'


    def parse_env(self, optional = False):
        self._data_env = None
        args.parse_var(self.parser, 'environment', str, 'environment name', optional)

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


    def parse_env_fields(self, optional = False):
        excluded_fields = ('created', 'updated')
        required = [x for x in self._env.required if x not in excluded_fields]
        optional = [x for x in self._env.optional if x not in excluded_fields]

        args.parse_key_values(self.parser, 
            'env_fields',
            'field=value',
            "\n".join(text.wrap("environment fields as key value pairs\n\ncreate required: {}\n\nupdate available: {}".format(", ".join(required), ", ".join(optional)), 60)), 
            optional
        )

    @property
    def env_fields(self):
        return self.options['env_fields']


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
