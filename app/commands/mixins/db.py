from django.conf import settings
from django.db import connections

from systems.db import manager
from systems.commands.index import CommandMixin
from utility.filesystem import filesystem_dir, filesystem_temp_dir, FileSystem
from utility.environment import Environment

import os
import re


class DatabaseMixin(CommandMixin('db')):

    backup_extension = '.tar.gz'


    @property
    def db(self):
        if not getattr(self, '_cached_db_manager', None):
            self._cached_db_manager = manager.DatabaseManager()
        return self._cached_db_manager


    @property
    def db_settings(self):
        return settings.DATABASES['default']

    @property
    def db_host(self):
        return self.db_settings['HOST']

    @property
    def db_port(self):
        return self.db_settings['PORT']

    @property
    def db_user(self):
        return self.db_settings['USER']

    @property
    def db_name(self):
        return self.db_settings['NAME']


    @property
    def snapshot_path(self):
        return self.manager.snapshot_path

    def get_snapshots(self):
        snapshots = []
        with filesystem_dir(self.snapshot_path) as path:
            for name in sorted(path.listdir(), reverse = True):
                if name.startswith("{}-snapshot-".format(settings.APP_NAME)) and name.endswith(self.backup_extension):
                    snapshots.append(name.rstrip(self.backup_extension))
        return snapshots

    def create_snapshot(self):
        snapshot_name = "{}-snapshot-{}".format(settings.APP_NAME, self.time.now_string)
        snapshot_file = os.path.join(self.snapshot_path, snapshot_name)
        module_disk = FileSystem(self.manager.module_path)
        files_disk = FileSystem(self.manager.file_path)
        active_env = Environment.get_active_env()

        self.send('core:db:backup:init', snapshot_name)

        with filesystem_temp_dir(self.get_temp_path(active_env)) as temp:
            self.info('Backing up application modules')
            module_disk.clone(temp.path('modules'))

            self.info('Backing up application database')
            self.clean_logs()
            self.dump('db.tar', temp.base_path)

            self.info('Backing up application files')
            files_disk.clone(temp.path('files'), ignore = self.manager.backup_ignore)

            temp.archive(snapshot_file)

        self.send('core:db:backup:complete', snapshot_name)
        self.success("Successfully dumped snapshot: {}".format(snapshot_name))

    def restore_snapshot(self, snapshot_name = None):
        if snapshot_name is None:
            snapshots = self.get_snapshots()
            if not snapshots:
                self.error("No snapshots found to restore")
            snapshot_name = snapshots[0]
            latest = True
        else:
            snapshot_name = snapshot_name.removesuffix(self.backup_extension)
            latest = False

        self.send('core:db:restore:init', {
            'name': snapshot_name,
            'latest': latest
        })
        self.disconnect_db()

        snapshot_file = os.path.join(self.snapshot_path, "{}{}".format(snapshot_name, self.backup_extension))
        module_disk = FileSystem(self.manager.module_path)
        files_disk = FileSystem(self.manager.file_path)
        active_env = Environment.get_active_env()

        with filesystem_temp_dir(self.get_temp_path(active_env)) as temp:
            self.info('Extracting application backup package')
            FileSystem.extract(snapshot_file, temp.base_path)

            self.info('Restoring application modules')
            for directory in module_disk.listdir():
                module_disk.remove(directory)
            for directory in temp.listdir('modules'):
                temp.get(directory, 'modules').clone(module_disk.path(directory))

            self.info('Restoring application database')
            self.drop_tables()
            self.restore('db.tar', temp.base_path)

            self.info('Restoring application files')
            for directory in temp.listdir('files'):
                files_disk.remove(directory)
                temp.get(directory, 'files').clone(files_disk.path(directory))

        self.send('core:db:restore:complete', {
            'name': snapshot_name,
            'latest': latest
        })
        self.success("Successfully restored snapshot: {}".format(snapshot_name))

    def clean_snapshots(self, keep_num = None):
        if keep_num is None:
            keep_num = settings.DB_SNAPSHOT_RENTENTION

        snapshot_disk = FileSystem(self.snapshot_path)
        for index, snapshot in enumerate(self.get_snapshots()):
            if index >= keep_num:
                self.notice("Removing snapshot: {}".format(snapshot))
                snapshot_disk.remove("{}{}".format(snapshot, self.backup_extension))

        self.send('core:db:clean', keep_num)


    @property
    def root_lib_path(self):
        return settings.ROOT_LIB_DIR

    def get_temp_path(self, env_name):
        return os.path.join(self.root_lib_path, 'tmp', env_name)


    def _get_auth_options(self):
        return [
            "--host={}".format(self.db_host),
            "--port={}".format(self.db_port),
            "--username={}".format(self.db_user),
            "--dbname={}".format(self.db_name)
        ]

    def _get_environment(self):
        return {
            'PGPASSWORD': self.db_settings['PASSWORD']
        }


    def disconnect_db(self):
        self.log_result = False
        connections.close_all()


    def query(self, query):
        self.sh(['psql', '--echo-all', '--expanded', '-c', query,
                *self._get_auth_options()
            ],
            env = self._get_environment(),
            line_prefix = '[psql] '
        )

    def dump(self, file, directory):
        self.sh(['pg_dump', '--verbose', '--blobs', '--inserts',
                '-f', file,
                '--format=t',
                *self._get_auth_options()
            ],
            cwd = directory,
            env = self._get_environment(),
            line_prefix = '[pg_dump] '
        )

    def restore(self, file, directory):
        self.sh(['pg_restore', '--verbose', '--no-owner',
                '--format=t',
                "--role={}".format(self.db_user),
                *self._get_auth_options(),
                file
            ],
            cwd = directory,
            env = self._get_environment(),
            line_prefix = '[pg_restore] '
        )

    def drop_tables(self):
        self.query(re.sub(r'\s+', ' ', " \
            DO $$ DECLARE r RECORD; \
            BEGIN \
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP \
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE'; \
                END LOOP; \
            END $$; \
        ".strip()))
