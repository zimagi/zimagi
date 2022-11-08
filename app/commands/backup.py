from systems.commands.index import Command
from utility.filesystem import filesystem_dir, FileSystem


class Backup(Command('backup')):

    def exec(self):
        lib_disk = FileSystem(self.lib_path)

        with filesystem_dir(self.snapshot_file) as package:
            self.info('Backing up application database')
            self.dump('db.tar', package.base_path)

            self.info('Backing up application libraries')
            lib_disk.clone(package.path('lib'), ignore = 'snapshots')
            package.archive()
            package.delete()

        self.success("Successfully dumped snapshot: {}".format(self.file_name))
