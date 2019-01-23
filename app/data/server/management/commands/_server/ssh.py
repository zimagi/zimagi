from systems.command import types, mixins
from utility.temp import temp_dir

import subprocess


class SSHCommand(
    mixins.data.ServerMixin,
    types.ServerActionCommand
):
    def get_description(self, overview):
        if overview:
            return """SSH into an existing server

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """SSH into an existing server
                      
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
        self.parse_server_name()

    def exec(self):
        server = self.server
        self.silent_data('ip', server.ip)
        self.silent_data('user', server.user)
        self.silent_data('password', server.password)
        self.silent_data('private_key', server.private_key)
    
    def postprocess(self, result):
        with temp_dir() as temp:
            ssh_command = ["ssh -t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"]
            destination = "{}@{}".format(
                result.get_named_data('user'), 
                result.get_named_data('ip')
            )            
            password = result.get_named_data('password')
            private_key = result.get_named_data('private_key')

            if password:
                ssh_command = [
                    "sshpass -p '{}'".format(password)
                ] + ssh_command
           
            if private_key:
                ssh_command.append("-i '{}'".format(
                    temp.save(private_key)
                ))
            
            ssh_command.append(destination)
            subprocess.call(" ".join(ssh_command), shell = True)
