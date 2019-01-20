from django.conf import settings

from .base import BaseTaskProvider
from .mixins import cli

import copy


class Command(
    cli.CLITaskMixin, 
    BaseTaskProvider
):
    def execute(self, results, servers, main_params):
        def exec_server(server, state):
            params = copy.deepcopy(main_params)

            if 'command' in self.config:
                command = self.config['command']
            else:
                self.command.error("Command task provider must have a 'command' property specified")

            sudo = self.config.get('sudo', False)
            lock = self.config.get('lock', False)
            args = self.config.get('args', [])
            options = self.config.get('options', {})
            options['_separator'] = self.config.get('option_seperator', ' ')
            
            self._parse_args(args, params.pop('args', None), lock)
            self._parse_options(options, params, lock)
            self._ssh_exec(server, command, args, options, sudo = sudo)

        self.command.run_list(servers, exec_server)
