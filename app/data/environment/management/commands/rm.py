
from systems.command.types import action
from systems.command import mixins


class Command(
    mixins.op.RemoveMixin,
    action.ActionCommand
):
    def server_enabled(self):
        return False

    def get_priority(self):
        return 8

    def get_command_name(self):
        return 'rm'

    def get_description(self, overview):
        if overview:
            return """remove an existing cluster environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """remove an existing cluster environment
                      
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
        self.parse_env()

    def confirm(self):
        if self._env.retrieve(self.env_name):
            self.confirmation("Are you sure you want to remove environment {}".format(self.env_name))       

    def exec(self):
        self.exec_rm(self._env, self.env_name)
        self._check_env()

    def _check_env(self):
        curr_env = self.get_env()
        if curr_env and self.env == curr_env.value:
            self.delete_env()
