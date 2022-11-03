from django.conf import settings
from django.db import connections

from systems.db import manager
from systems.commands.index import CommandMixin

import os
import re


class DatabaseMixin(CommandMixin('db')):

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

    @property
    def snapshot_file(self):
        return os.path.join(self.snapshot_path, self.file_name)


    @property
    def root_lib_path(self):
        return settings.ROOT_LIB_DIR

    def get_temp_path(self, env_name):
        return os.path.join(self.root_lib_path, 'tmp', env_name)


    @property
    def lib_path(self):
        return self.manager.lib_path


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
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP \
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE'; \
                END LOOP; \
            END $$; \
        ".strip()))
