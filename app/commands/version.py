from django.conf import settings

from systems.commands.index import Command


class Version(Command('version')):

    def exec(self):
        env = self.get_env()

        if not settings.API_EXEC:
            self.table(self.render_list(self._environment, filters = {
                'name': env.name
            }))
            self.info('')
            self.data("> Client version", self.get_version(), 'client_version')

            if env.host and env.user and env.token:
                result = self.exec_remote(env, 'version', display = False)

                self.table([
                    [self.key_color("Server version"), result.named['server_version'].data],
                    [self.key_color("Server environment"), result.named['server_env'].data],
                    [self.key_color("Server runtime repository"), result.named['server_repo'].data],
                    [self.key_color("Server runtime image"), result.named['server_image'].data]
                ])

                if env.name != result.named['server_env'].data:
                    self.warning("Local and remote environment names do not match.  Use remote environment name locally to avoid sync issues.")
        else:
            self.silent_data('server_version', self.get_version())
            self.silent_data('server_env', env.name)
            self.silent_data('server_repo', env.repo)
            self.silent_data('server_image', env.base_image)
