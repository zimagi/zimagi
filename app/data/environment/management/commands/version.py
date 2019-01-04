from systems.command import types, mixins


class Command(
    types.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'version'

    def get_description(self, overview):
        if overview:
            return """get client and all environment versions

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """get client and all environment versions
                      
Etiam mattis iaculis felis eu pharetra. Nulla facilisi. 
Duis placerat pulvinar urna et elementum. Mauris enim risus, 
mattis vel risus quis, imperdiet convallis felis. Donec iaculis 
tristique diam eget rutrum.

Etiam sit amet mollis lacus. Nulla pretium, neque id porta feugiat, 
erat sapien sollicitudin tellus, vel fermentum quam purus non sem. 
Mauris venenatis eleifend nulla, ac facilisis nulla efficitur sed. 
Etiam a ipsum odio. Curabitur magna mi, ornare sit amet nulla at, 
scelerisque tristique leo. Curabitur ut faucibus leo, non tincidunt 
velit. Aenean sit amet consequat mauris.
"""
    def server_enabled(self):
        return True

    def remote_exec(self):
        return False

    def exec(self):
        if not self.api_exec:
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
