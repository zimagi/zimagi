from django.conf import settings

from systems.command.types import environment


class Command(
    environment.EnvironmentActionCommand
):
    def get_priority(self):
        return 1000

    def server_enabled(self):
        return True

    def remote_exec(self):
        return False

    def exec(self):
        env = self.get_env()

        if not settings.API_EXEC:
            self.table(self._env.render_list(self, filters = {
                'name': env.name
            }))
            self.info('')
            self.data("> Client version", self.get_version(), 'client_version')

            if env.host and env.user and env.token:
                result = self.exec_remote(env, 'version', display = False)

                self.data("> Server version",
                    result.named['server_version'].data
                )
                self.data("> Server environment",
                    result.named['server_env'].data
                )
                self.data("> Server runtime repository",
                    result.named['server_repo'].data
                )
                self.data("> Server runtime image",
                    result.named['server_image'].data
                )
                if env.name != result.named['server_env'].data:
                    self.warning("Local and remote environment names do not match.  Use remote environment name locally to avoid sync issues.")
        else:
            self.silent_data('server_version', self.get_version())
            self.silent_data('server_env', env.name)
            self.silent_data('server_repo', env.repo)
            self.silent_data('server_image', env.base_image)
