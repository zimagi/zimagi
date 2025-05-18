import os

from systems.plugins.index import BaseProvider
from utility.data import ensure_list


class Provider(BaseProvider("task", "remote_script")):
    def execute(self, results, params):
        script_path = self.get_path(self.field_script)

        if not os.path.exists(script_path):
            self.command.error(f"Remote script task provider file {script_path} does not exist")

        script_base, script_ext = os.path.splitext(script_path)
        temp_path = f"/tmp/{self.generate_name(24)}{script_ext}"

        env = self._env_vars(params)
        options = self._merge_options(self.field_options, params, self.field_lock)
        args = ensure_list(self.field_args, [])

        ssh = self._get_ssh(env)
        ssh.upload(script_path, temp_path, mode=755)
        try:
            self._ssh_exec(temp_path, self._interpolate(args, options), sudo=self.field_sudo, ssh=ssh)
        finally:
            ssh.exec("rm -f", temp_path)
