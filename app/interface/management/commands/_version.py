from systems.command import types, mixins
from utility.config import RuntimeConfig


class Command(
    types.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'version'

    def server_enabled(self):
        return True

    def remote_exec(self):
        return False

    def exec(self):
        if not RuntimeConfig.api():
            self.data("Client version", self.get_version(), 'client_version')

            env_versions = [['name', 'host', 'version']]

            for env in self._env.all():
                name = env.name
                host = env.host
                
                if host:
                    result = self.exec_remote(env, 'version', display = False)
                    version = result.named['server_version'].data
                else:
                    version = self.get_version()

                env_versions.append([name, host, version])

            self.info("\nEnvironment versions:")
            self.table(env_versions, 'environment_versions')
        else:
            self.data("Server version", self.get_version(), 'server_version')
