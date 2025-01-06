from systems.plugins.index import ProviderMixin


class SSHTaskMixin(ProviderMixin("ssh_task")):
    def _get_ssh(self, env=None):
        if not env:
            env = {}

        return self.command.ssh(
            self.field_host,
            self.field_user,
            password=self.secret_password,
            key=self.secret_private_key,
            timeout=self.field_timeout,
            port=self.field_port,
            env=env,
        )

    def _ssh_exec(self, command, args=None, options=None, env=None, sudo=False, ssh=None):
        if not args:
            args = []
        if not options:
            options = {}

        if ssh is None:
            ssh = self._get_ssh(env)

        if sudo:
            ssh.sudo(command, *args, **options)
        else:
            ssh.exec(command, *args, **options)
