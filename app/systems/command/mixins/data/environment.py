
from data.environment import models


class EnvironmentMixin(object):

    def parse_env(self):
        self.parser.add_argument(
            'environment', 
            nargs = 1, 
            type = str, 
            help = "environment name"
        )

    @property
    def env(self):
        return self.options['environment'][0]


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
