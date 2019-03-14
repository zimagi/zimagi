from django.conf import settings

from .base import BaseProvider
from .mixins import cli

import os
import copy


class Provider(
    cli.CLITaskMixin,
    BaseProvider
):
    def execute(self, results, servers, main_params):
        def exec_server(server):
            params = copy.deepcopy(main_params)

            if 'script' in self.config:
                script_path = self.get_path(self.config['script'])
            else:
                self.command.error("Script task provider must have a 'script' property specified that links to an executable file")

            if not os.path.exists(script_path):
                self.command.error("Script task provider file {} does not exist".format(script_path))

            script_base, script_ext = os.path.splitext(script_path)
            temp_path = "/tmp/{}{}".format(self.generate_name(24), script_ext)

            lock = self.config.get('lock', False)
            args = self.config.get('args', [])
            options = self.config.get('options', {})
            options['_separator'] = self.config.get('option_seperator', ' ')

            ssh = server.provider.ssh()
            ssh.upload(script_path, temp_path, mode = 0o700)
            try:
                self._parse_args(args, params.pop('args', None), lock)
                self._parse_options(options, params, lock)
                self._ssh_exec(server, temp_path, args, options,
                    sudo = self.config.get('sudo', False),
                    ssh = ssh
                )
            finally:
                ssh.sudo('rm -f', temp_path)

        self.command.run_list(servers, exec_server)
