from systems.commands.index import Command
from utility.filesystem import filesystem_temp_dir, FileSystem
from utility.environment import Environment


class Restore(Command('restore')):

    def exec(self):
        self.disconnect_db()

        lib_disk = FileSystem(self.lib_path)
        active_env = Environment.get_active_env()

        with filesystem_temp_dir(self.get_temp_path(active_env)) as temp:
            self.info('Extracting application backup package')
            FileSystem.extract(
                "{}.tar.gz".format(self.snapshot_file.removesuffix('.tar.gz')),
                temp.base_path
            )
            self.info('Restoring application database')
            self.drop_tables()
            self.restore('db.tar', temp.base_path)

            self.info('Restoring application libraries')
            for name in temp.listdir('lib'):
                lib_disk.remove(name)
                temp.get(name, 'lib').clone(lib_disk.path(name))

        self.success("Successfully restored snapshot: {}".format(self.file_name))
