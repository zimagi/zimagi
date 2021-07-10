from django.conf import settings

from systems.commands.index import Command


class Version(Command('version')):

    def exec(self):
        env = self.get_env()

        if not settings.API_EXEC:
            version_info = [
                [self.key_color("Client version"), self.value_color(self.get_version())]
            ]

            self.table(self.render_list(self._environment, filters = {
                'name': env.name
            }))

            if env.host and env.user and env.token:
                result = self.exec_remote(env, 'version', display = False)

                version_info.extend([
                    [self.key_color("Host version"), self.value_color(result.named['host_version'].data)],
                    [self.key_color("Host environment"), result.named['host_env'].data],
                    [self.key_color("Host runtime repository"), result.named['host_repo'].data],
                    [self.key_color("Host runtime image"), result.named['host_image'].data]
                ])

                if env.name != result.named['host_env'].data:
                    self.warning("Local and remote environment names do not match.  Use remote environment name locally to avoid sync issues.")

            self.table(version_info)
        else:
            self.silent_data('host_version', self.get_version())
            self.silent_data('host_env', env.name)
            self.silent_data('host_repo', env.repo)
            self.silent_data('host_image', env.base_image)
