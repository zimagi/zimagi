from systems.command.base import command_list
from systems.command import types, factory
from utility.temp import temp_dir

import subprocess


class RotateCommand(
    types.ServerActionCommand
):
    def parse(self):
        self._server.parse_scopes(self)
        self.parse_server_search(True)

    def exec(self):
        self._server.set_scopes(self)

        def rotate_server(server):
            self.data("Rotating SSH keypair for", str(server))
            server.provider.rotate_password()
            server.provider.rotate_key()
            server.save()

        self.run_list(self.server_instances, rotate_server)


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
        base_name = self.get_command_name()
        return command_list(
            factory.ResourceCommandSet(types.ServerActionCommand, base_name,
                save_multiple = True
            ),
            ('rotate', RotateCommand),
            ('ssh', SSHCommand)
        )
