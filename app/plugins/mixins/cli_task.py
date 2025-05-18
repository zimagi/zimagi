from systems.plugins.index import ProviderMixin
from utility.data import env_value


class CLITaskMixin(ProviderMixin("cli_task")):
    def _env_vars(self, params):
        return self.command.options.interpolate(env_value(self._merge_options(self.field_env, params.pop("env", {}))))
