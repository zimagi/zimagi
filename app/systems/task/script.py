from django.conf import settings

from .base import BaseTaskProvider

import os


class Script(BaseTaskProvider):

    def execute(self, results, servers):
        def exec_server(server, state):
            if 'script' in self.config:
                script_path = self.get_path(self.config['script'])
            else:
                self.command.error("Script task provider must have a 'script' property specified that links to an executable file")

            if not os.path.exists(script_path):
                self.command.error("Script task provider file {} does not exist".format(script_path))

            script_base, script_ext = os.path.splitext(script_path)
            script_temp_path = "/tmp/{}{}".format(self.generate_name(24), script_ext)
            script_sudo = self.config.get('sudo', False)
            
            script_args = self.config.get('args', [])
            script_options = self.config.get('options', {})
            script_options['_separator'] = self.config.get('option_seperator', ' ')
            
            ssh = server.compute_provider.ssh()
            ssh.upload(script_path, script_temp_path, mode = 0o700)
            try:
                if script_sudo:
                    ssh.sudo(script_temp_path, *script_args, **script_options)
                else:
                    ssh.exec(script_temp_path, *script_args, **script_options)
            finally:
                ssh.sudo('rm -f', script_temp_path)

        self.command.run_list(servers, exec_server)
