from systems.plugins.index import BaseProvider

import os


class Provider(BaseProvider('task', 'upload')):

    def execute(self, results, params):
        file_path = self.get_path(self.field_file)

        if not os.path.exists(file_path):
            self.command.error("Upload task provider file {} does not exist".format(file_path))

        ssh = self._get_ssh()
        ssh.upload(file_path, self.field_remote_path,
            mode = self.field_mode,
            owner = self.field_owner,
            group = self.field_group
        )
