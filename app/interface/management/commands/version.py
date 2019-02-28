from systems.command import types, mixins
from utility.config import RuntimeConfig


class Command(
    types.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'version'

    def get_priority(self):
        return 1000

    def server_enabled(self):
        return True

    def remote_exec(self):
        return False

    def exec(self):
        if not RuntimeConfig.api():
            env = self.get_env()
            self.table(self._env.render_list(self, filters = {
                'name': env.name
            }))
            self.info('')
            self.data("> Client version", self.get_version(), 'client_version')           
            
            if env.host and env.user and env.token:
                result = self.exec_remote(env, 'version', display = False)
                version = result.named['server_version'].data               
                self.data("> Server version", version, 'server_version')
        else:
            self.silent_data('server_version', self.get_version())
