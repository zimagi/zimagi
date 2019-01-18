from django.conf import settings

from .base import BaseTaskProvider


class Command(BaseTaskProvider):

    def execute(self, results, servers):
        def exec_server(server, state):
            if 'command' in self.config:
                command = self.config['command']
            else:
                self.command.error("Command task provider must have a 'command' property specified")

            command_sudo = self.config.get('sudo', False)
            command_args = self.config.get('args', [])
            command_options = self.config.get('options', {})
            command_options['_separator'] = self.config.get('option_seperator', ' ')
            
            ssh = server.compute_provider.ssh()
            if command_sudo:
                ssh.sudo(command, *command_args, **command_options)
            else:
                ssh.exec(command, *command_args, **command_options)

        self.command.run_list(servers, exec_server)
