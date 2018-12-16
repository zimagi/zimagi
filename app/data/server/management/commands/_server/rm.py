
from systems.command.types import action
from systems.command import mixins


class RemoveCommand(
    mixins.op.RemoveMixin,
    mixins.data.ServerMixin, 
    action.ActionCommand
):
    def get_description(self, overview):
        if overview:
            return """remove an existing server in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """remove an existing server in current environment
                      
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
    def parse(self):
        self.parse_server()

    def confirm(self):
        if self._server.retrieve(self.server_name):
            self.confirmation("Are you sure you want to remove server {}".format(self.server_name))       

    def exec(self):
        self.exec_rm(self._server, self.server_name)
