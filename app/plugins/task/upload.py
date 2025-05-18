import os

from systems.plugins.index import BaseProvider


class Provider(BaseProvider("task", "upload")):
    def execute(self, results, params):
        file_path = self.get_path(self.field_file)

        if not os.path.exists(file_path):
            self.command.error(f"Upload task provider file {file_path} does not exist")

        ssh = self._get_ssh()
        ssh.upload(file_path, self.field_remote_path, mode=self.field_mode, owner=self.field_owner, group=self.field_group)
