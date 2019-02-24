from django.conf import settings

from systems.command import types, mixins


class Command(
    mixins.data.ServerMixin,
    types.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'deploy'

    def server_enabled(self):
        return True
    
    def parse(self):
        self.parse_network_name('--network')
        self.parse_server_name()

    def exec(self):
        self.set_server_scope()
        server = self.server
        
        env = self.get_env()
        env.host = server.ip
        env.token = settings.DEFAULT_ADMIN_TOKEN
        #env.save()

        self.data("Deploying cenv system to server", str(server))    
        #self.project.provider.exec_task('bootstrap', server)

        self.exec_remote(env, 'db restore', {
            'host': server.ip,
            'token': settings.DEFAULT_ADMIN_TOKEN
        }, display = True)
        