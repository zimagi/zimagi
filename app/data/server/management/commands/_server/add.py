from django.conf import settings

from systems.command import types, mixins


class AddCommand(
    mixins.op.AddMixin,
    mixins.data.ServerMixin, 
    types.ServerActionCommand
):
    def get_description(self, overview):
        if overview:
            return """add a new server in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """add a new server in current environment
                      
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
    def server_field_help(self):
        help = ["server fields as key value pairs (by provider)", ' ']

        def render(messages = '', prefix = ''):
            if not isinstance(messages, (tuple, list)):
                messages = [messages]

            for message in messages:
                help.append("{}{}".format(prefix, message))

        for name, provider in settings.CLOUD_PROVIDERS.items():
            cloud = self.cloud(name)
            schema = cloud.server_schema()

            render(("provider_name: {} ({})".format(self.success_color(name), cloud.name), ' '))

            if schema['requirements']:
                render('requirements:', '  ')
                for require in schema['requirements']:
                    render("{} - {}".format(self.warning_color(require['name']), require['help']), '    ')
                render()

            if schema['options']:
                render('options:', '  ')
                for option in schema['options']:
                    render("{} ({}) - {}".format(self.warning_color(option['name']), self.success_color(str(option['default'])), option['help']), '    ')

            render()

        return help


    def parse(self):
        self.parse_provider_name()
        self.parse_server_groups(True)
        self.parse_server_fields(True, self.server_field_help)

    def exec(self):
        def complete_callback(server):
            self.success(server)

            instance = self.exec_add(self._server, server.name, {
                'config': server.config,
                'type': server.type,
                'region': server.region,
                'ip': server.ip,
                'user': server.user,
                'password': server.password,
                'private_key': server.private_key,
                'data_device': server.data_device
            })
            self.exec_add_related(
                self._server_group, 
                instance, 'groups', 
                server.groups
            )

        self.provider.create_servers(
            self.server_fields, 
            self.server_group_names, 
            complete_callback
        )        
