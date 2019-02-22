from django.conf import settings

from . import DataMixin
from systems.db import manager


class DatabaseMixin(DataMixin):

    def parse_db_dir(self, optional = '--dir', help_text = 'database directory within project'):
        self.parse_variable('db_dir', optional, str, help_text, 'NAME', 'db')

    @property
    def db_dir(self):
        return self.options.get('db_dir', 'db')


    def parse_file_name(self, optional = False, help_text = 'database file name within project'):
        self.parse_variable('file_name', optional, str, help_text, 'NAME')

    @property
    def file_name(self):
        return self.options.get('file_name', None)

    @property
    def db_file_path(self, project):
        file_location = os.path.join(self.db_dir, self.file_name)
        return project.project_path(file_location)


    def parse_no_encrypt(self, optional = '--no-encrypt', help_text = 'database file not encrypted'):
        self.parse_variable('no_encrypt', optional, bool, help_text)

    @property
    def no_encrypt(self):
        return self.options.get('no_encrypt', None)
    

    @property
    def db(self):
        if not getattr(self, '_cached_db_manager', None):
            self._cached_db_manager = manager.DatabaseManager()
        return self._cached_db_manager
