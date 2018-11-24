
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


    def delete_env(self):
        if self._state.delete_env():
            self.success(" > Successfully deleted environment state")
        else:
            self.error("Environment state deletion failed")
