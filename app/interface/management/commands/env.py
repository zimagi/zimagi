from django.conf import settings

from systems.command import types, mixins, factory


class SetCommand(
    types.EnvironmentActionCommand
):
    def parse(self):
        self.parse_env_repo('--repo')
        self.parse_env_image('--image')
        self.parse_env_name()

    def exec(self):
        self.set_env(self.env_name, self.env_repo, self.env_image)


class DeployCommand(
    mixins.data.ServerMixin,
    types.EnvironmentActionCommand
):
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


class Command(
    types.EnvironmentRouterCommand
):
    def get_command_name(self):
        return 'env'

    def get_subcommands(self):
        parent = types.EnvironmentActionCommand
        base_name = self.get_command_name()
        name_field = 'curr_env_name'
        return (
            ('list', factory.ListCommand(parent, base_name)),
            ('get', factory.GetCommand(
                parent, base_name,
                name_field = name_field
            )),
            ('set', SetCommand),
            ('save', factory.SaveCommand(
                parent, base_name,
                provider_name = base_name,
                name_field = name_field
            )),
            ('rm', factory.RemoveCommand(
                parent, base_name,
                name_field = name_field,
                post_methods = {
                    'delete_env': None
                }
            ))
        )
