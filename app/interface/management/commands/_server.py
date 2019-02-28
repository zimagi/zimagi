from systems.command.base import command_list
from systems.command import types, factory
from utility.temp import temp_dir

import subprocess


class RotateCommand(
    types.ServerActionCommand
):
    def parse(self):
        self.parse_network_name('--network')
        self.parse_server_reference(True)

    def exec(self):
        self.set_server_scope()

        def rotate_server(server, state):
            self.data("Rotating SSH keypair for", str(server))
            
            server.provider.rotate_password()
            server.provider.rotate_key()            
            server.save()
        
        self.run_list(self.servers, rotate_server)


class SSHCommand(
    types.ServerActionCommand
):
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
            
            ssh_command.append("{}@{}".format(
                result.get_named_data('user'), 
                result.get_named_data('ip')
            ))
            subprocess.call(" ".join(ssh_command), shell = True)


class Command(types.ServerRouterCommand):

    def get_command_name(self):
        return 'server'

    def get_subcommands(self):
        return command_list(
            factory.ResourceCommandSet(
                types.ServerActionCommand, 'server',
                list_fields = (
                    ('name', 'Name'),
                    ('type', 'Type'),
                    ('subnet__network__name', 'Network'),
                    ('subnet__name', 'Subnet'),
                    ('ip', 'IP'),
                    ('user', 'User'),
                    ('status', 'Status')
                ),
                relations = { 
                    'group': 'groups', 
                    'firewall': 'firewalls' 
                },
                scopes = {
                    'network': '--network',
                    'subnet': '--subnet'
                }
            ),
            ('rotate', RotateCommand),
            ('ssh', SSHCommand)
        )
