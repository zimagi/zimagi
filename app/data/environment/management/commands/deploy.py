from django.conf import settings

from systems.command import types, mixins


class Command(
    mixins.data.ServerMixin,
    types.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'deploy'

    def get_description(self, overview):
        if overview:
            return """deploy the cenv system to a standalone server

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """deploy the cenv system to a standalone server
                      
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
    
    def parse(self):
        self.parse_network_name('--network')
        self.parse_server_name()

    def exec(self):
        self.set_server_scope()
        server = self.server
        
        env = self.curr_env
        env.host = server.ip
        env.token = settings.DEFAULT_ADMIN_TOKEN
        #env.save()

        self.data("Deploying cenv system to server", str(server))    
        #self.project.provider.exec_task('bootstrap', server)

        self.exec_remote(env, 'db restore', {
            'host': server.ip,
            'token': settings.DEFAULT_ADMIN_TOKEN
        }, display = True)
        