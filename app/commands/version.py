from django.conf import settings

from systems.commands.index import Command


class Version(Command('version')):

    def exec(self):
        env = self.get_env()
        host = self.get_host()

        if not settings.API_EXEC:
            self.notice("Environment Information")
            self.table([
                [self.key_color("Name"), self.value_color(env.name)],
                [self.key_color("Image Repository"), self.value_color(str(env.repo))],
                [self.key_color("Base Image"), self.value_color(str(env.base_image))],
                [self.key_color("Runtime Image"), self.value_color(str(env.runtime_image))],
                [self.key_color("Created"), self.value_color(self.format_time(env.created))],
                [self.key_color("Updated"), self.value_color(self.format_time(env.updated))]
            ])
            self.info('')

            version_info = [
                [self.key_color("Client version"), self.value_color(self.get_version())]
            ]
            if host:
                result = self.exec_remote(host, 'version', display = False)

                version_info.extend([
                    [self.key_color("Host version"), self.value_color(result.named['host_version'].data)],
                    [self.key_color("Host environment"), result.named['host_env'].data],
                    [self.key_color("Host runtime repository"), result.named['host_repo'].data],
                    [self.key_color("Host runtime image"), result.named['host_image'].data]
                ])
            self.table(version_info)
        else:
            self.silent_data('host_version', self.get_version())
            self.silent_data('host_env', env.name)
            self.silent_data('host_repo', env.repo)
            self.silent_data('host_image', env.base_image)
